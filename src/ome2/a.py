import math
import geopandas as gpd
from shapely.geometry import LineString,Point
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


#print("loading...")
gdf = gpd.read_file(out_folder+"test.gpkg")
print(len(gdf))
#print(gdf.dtypes)

#create graph
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


#make list of nodes
nodes = []
for node in graph.nodes(): nodes.append(node)

#index nodes
spatial_index = index.Index()
for i in range(graph.number_of_nodes()):
    node = nodes[i]
    c = node.split('_'); x=float(c[0]); y=float(c[1])
    spatial_index.insert(i, (x,y,x,y))


#idx = index.Index()
#idx.insert(4321, (34.37, 26.73, 49.37, 41.73), obj=42)
#hits = idx.nearest((0, 0, 10, 10), 3)
#print(next(hits))

#center
xC = 3025000 
yC = 3935000
#radius
rad = 5000

nb = 20
for i in range(nb):
    angle = 2*math.pi*i/nb
    x = xC+rad*math.cos(angle)
    y = xC+rad*math.sin(angle)
    node = index.nearest((x, y, x, y), 1)
    node = next(node)
    print(x,y,node)

    



#compute shortest path
sp = nx.shortest_path(graph, "3931227_3026428", "3936658_3029248", weight="weight")
wt = nx.shortest_path_length(graph, "3931227_3026428", "3936658_3029248", weight="weight")
#print(sp)
#print(wt)

#export as geopackage
line = getShortestPathGeometry(sp)
f = {'geometry': [line], 'duration': [wt]}
gdf = gpd.GeoDataFrame(f)
gdf.crs = 'EPSG:3035'
gdf.to_file(out_folder+"sp.gpkg", driver="GPKG")
