import math
import geopandas as gpd
from shapely.geometry import Point,LineString
from shapely.errors import GEOSException
import networkx as nx
from rtree import index
from datetime import datetime

out_folder = '/home/juju/Bureau/gisco/OME2_analysis/'

#network analysis libs:
#NetworkX: https://networkx.org/documentation/stable/reference/algorithms/shortest_paths.html
#igraph: C with interfaces for Python. https://python.igraph.org/en/stable/api/igraph.GraphBase.html#get_shortest_path
#Graph-tool: implemented in C++ with a Python interface. https://graph-tool.skewed.de/static/doc/topology.html


def get_shortest_path_geometry(sp):
    coordinates_tuples = [tuple(map(float, coord.split('_'))) for coord in sp]
    return LineString(coordinates_tuples)

def getNodeCoordinate(node):
    c = node.split('_')
    x=float(c[0]); y=float(c[1])
    return [x,y]

print("loading", datetime.now())
xMin = 3900000
yMin = 3000000 
size = 10000
resolution = 1000
gdf = gpd.read_file(out_folder+"test_"+str(size)+".gpkg")
print(str(len(gdf)) + " links")
#print(gdf.dtypes)

print("make graph", datetime.now())
graph = nx.Graph()
for i, f in gdf.iterrows():
    g = f.geometry
    pi = g.coords[0]
    pi = str(round(pi[0])) +'_'+ str(round(pi[1]))
    pf = g.coords[-1]
    pf = str(round(pf[0])) +'_'+ str(round(pf[1]))
    speedKmH = 50
    w = round(g.length / speedKmH*3.6)
    #print(pi, pf, w)
    graph.add_edge(pi, pf, weight=w)

#clear memory
del gdf


print("make list of nodes", datetime.now())
nodes = []
for node in graph.nodes(): nodes.append(node)

print("make spatial index", datetime.now())
idx = index.Index()
for i in range(graph.number_of_nodes()):
    node = nodes[i]
    [x,y] = getNodeCoordinate(node)
    idx.insert(i, (x,y,x,y))

print("compute shortest paths", datetime.now())

#origin node: center
node1 = nodes[next(idx.nearest((xMin+size/2, yMin+size/2, xMin+size/2, yMin+size/2), 1))]

#used for A* heuristic
def dist(a, b):
    [x1, y1] = getNodeCoordinate(a); [x2, y2] = getNodeCoordinate(b)
    #return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
    return math.abs(x1-x2)+math.abs(y1-y2)

nb = math.ceil(size/resolution)
sp_geometries = []; sp_durations = []
pt_geometries = []; pt_durations = []; pt_resolutions = []
seg_geometries = []; seg_lengths = []
for i in range(nb+1):
    for j in range(nb+1):
        #compute shortest path
        #angle = 2*math.pi*i/nb
        #x = round(xC+rad*math.cos(angle))
        #y = round(yC+rad*math.sin(angle))
        x = xMin + i*resolution
        y = yMin + j*resolution
        node = idx.nearest((x, y, x, y), 1)
        node = next(node)
        node = nodes[node]

        #compute distance to network node
        [xN,yN]=getNodeCoordinate(node)
        segg = LineString([(x, y), (xN, yN)])
        distNetw = segg.length

        #point information
        pt_geometries.append(Point(x,y))
        pt_resolutions.append(resolution)
        ptdur = math.inf

        #network segment information
        seg_geometries.append(segg)
        seg_lengths.append(distNetw)
        try:
            #default
            sp = nx.shortest_path(graph, node1, node, weight="weight")
            #A*
            #sp = nx.astar_path(graph, node1, node, heuristic=dist, weight="weight")

            line = get_shortest_path_geometry(sp)
            sp_geometries.append(line)
            #wt = nx.shortest_path_length(graph, node1, node, weight="weight")
            wt = nx.path_weight(graph, sp, weight='weight')
            sp_durations.append(wt)
            ptdur = wt
        except nx.NetworkXNoPath as e:
            print("Exception NetworkXNoPath:", e)
        except GEOSException as e:
            print("Exception GEOSException:", e)
        pt_durations.append(ptdur)

print("export paths as geopackage", len(sp_geometries), datetime.now())
fs = {'geometry': sp_geometries, 'duration': sp_durations}
gdf = gpd.GeoDataFrame(fs)
gdf.crs = 'EPSG:3035'
gdf.to_file(out_folder+"sp.gpkg", driver="GPKG")

print("export points as geopackage", len(pt_geometries), datetime.now())
fs = {'geometry': pt_geometries, 'duration': pt_durations, 'resolution': pt_resolutions, 'netdist': seg_lengths}
gdf = gpd.GeoDataFrame(fs)
gdf.crs = 'EPSG:3035'
gdf.to_file(out_folder+"pt.gpkg", driver="GPKG")

print("export network segments as geopackage", len(seg_geometries), datetime.now())
fs = {'geometry': seg_geometries, 'dist': seg_lengths}
gdf = gpd.GeoDataFrame(fs)
gdf.crs = 'EPSG:3035'
gdf.to_file(out_folder+"seg.gpkg", driver="GPKG")
