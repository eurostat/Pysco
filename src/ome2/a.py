import math
import geopandas as gpd
from shapely.geometry import LineString
import networkx as nx
from rtree import index

out_folder = '/home/juju/Bureau/gisco/OME2_analysis/'

#network analysis libs:
#NetworkX: https://networkx.org/documentation/stable/reference/algorithms/shortest_paths.html
#igraph: C with interfaces for Python. https://python.igraph.org/en/stable/api/igraph.GraphBase.html#get_shortest_path
#Graph-tool: implemented in C++ with a Python interface. https://graph-tool.skewed.de/static/doc/topology.html


def getShortestPathGeometry(sp):
    coordinates_tuples = [tuple(map(float, coord.split('_'))) for coord in sp]
    return LineString(coordinates_tuples)


print("loading")
gdf = gpd.read_file(out_folder+"test.gpkg")
print(str(len(gdf)) + " links")
#print(gdf.dtypes)

print("make graph")
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


print("make list of nodes")
nodes = []
for node in graph.nodes(): nodes.append(node)

print("make spatial index")
idx = index.Index()
for i in range(graph.number_of_nodes()):
    node = nodes[i]
    c = node.split('_'); x=float(c[0]); y=float(c[1])
    idx.insert(i, (x,y,x,y))


#idx = index.Index()
#idx.insert(4321, (34.37, 26.73, 49.37, 41.73), obj=42)
#hits = idx.nearest((0, 0, 10, 10), 3)
#print(next(hits))

print("compute shortest paths")

#center - origin point
xC = 3935000
yC = 3025000 
#origin node
node1 = nodes[next(idx.nearest((xC, yC, xC, yC), 1))]

#radius
rad = 15000
nb = 20
geometries = []; durations = []
for i in range(nb):
    angle = 2*math.pi*i/nb
    x = round(xC+rad*math.cos(angle))
    y = round(yC+rad*math.sin(angle))
    node = idx.nearest((x, y, x, y), 1)
    node = next(node)
    node = nodes[node]

    #compute shortest path
    try:
        sp = nx.shortest_path(graph, node1, node, weight="weight")
        #TODO improve
        wt = nx.shortest_path_length(graph, node1, node, weight="weight")
        line = getShortestPathGeometry(sp)
        geometries.append(line)
        durations.append(wt)
    except nx.NetworkXNoPath as e:
        print("Exception:", e)


print("export as geopackage")
fs = {'geometry': geometries, 'duration': durations}
gdf = gpd.GeoDataFrame(fs)
gdf.crs = 'EPSG:3035'
gdf.to_file(out_folder+"sp.gpkg", driver="GPKG")
