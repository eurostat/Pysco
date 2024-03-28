import math
import geopandas as gpd
from shapely.geometry import LineString
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


print("loading", datetime.now())
gdf = gpd.read_file(out_folder+"test.gpkg")
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
    c = node.split('_'); x=float(c[0]); y=float(c[1])
    idx.insert(i, (x,y,x,y))

print("compute shortest paths", datetime.now())

#origin point
xC = 3900000
yC = 3000000 
#origin node
node1 = nodes[next(idx.nearest((xC, yC, xC, yC), 1))]

#radius
rad = 30000
nb = 50
geometries = []; durations = []
for i in range(nb):
    for j in range(nb):
        #angle = 2*math.pi*i/nb
        #x = round(xC+rad*math.cos(angle))
        #y = round(yC+rad*math.sin(angle))
        x = xC + i*60000/nb
        y = yC + j*60000/nb
        node = idx.nearest((x, y, x, y), 1)
        node = next(node)
        node = nodes[node]

        #compute shortest path
        try:
            sp = nx.shortest_path(graph, node1, node, weight="weight")
            #wt = nx.shortest_path_length(graph, node1, node, weight="weight")
            wt = nx.path_weight(graph, sp, weight='weight')
            line = get_shortest_path_geometry(sp)
            geometries.append(line)
            durations.append(wt)
        except nx.NetworkXNoPath as e:
            print("Exception:", e)


print("export as geopackage", datetime.now())
fs = {'geometry': geometries, 'duration': durations}
gdf = gpd.GeoDataFrame(fs)
gdf.crs = 'EPSG:3035'
gdf.to_file(out_folder+"sp.gpkg", driver="GPKG")
