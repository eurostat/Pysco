import geopandas as gpd
from shapely.geometry import LineString
import networkx as nx

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

#compute shortest path
sp = nx.shortest_path(graph, "3931227_3026428", "3936658_3029248", weight="weight")
wt = nx.shortest_path_length(graph, "3931227_3026428", "3936658_3029248", weight="weight")
#print(sp)
#print(wt)

#export as geopackage
line = getShortestPathGeometry(sp)
f = {'geometry': [line], 'duration': [wt]}
gdf = gpd.GeoDataFrame(f)
gdf = gdf.set_crs(3035)
print(gdf.crs)
gdf.to_file(out_folder+"sp.gpkg", driver="GPKG")

