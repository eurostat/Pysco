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

#index points
#spatial_index = index.Index()
#eps = 0.1
for i in range(graph.number_of_nodes()):
    node = graph.nodes.get(i)
    print(node)
    c = node.split('_'); x=float(c[0]); y=float(c[1])
    #bbox = Point(x, y).bounds
    #print(i, Point(x, y).bounds)
    #spatial_index.insert(0, (x,y,x,y))



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

