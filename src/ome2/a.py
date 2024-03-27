import geopandas as gpd
import networkx as nx

out_folder = '/home/juju/Bureau/gisco/OME2_analysis/'

#network analysis libs:
#NetworkX: https://networkx.org/documentation/stable/reference/algorithms/shortest_paths.html
#igraph: C with interfaces for Python. https://python.igraph.org/en/stable/api/igraph.GraphBase.html#get_shortest_path
#Graph-tool: implemented in C++ with a Python interface. https://graph-tool.skewed.de/static/doc/topology.html


#print("loading...")
#gdf = gpd.read_file(out_folder+"test.gpkg")
#print(len(gdf))


graph = nx.Graph()
graph.add_edge("A", "B", weight=4)
graph.add_edge("B", "D", weight=2)
graph.add_edge("A", "C", weight=3)
graph.add_edge("C", "D", weight=4)
sp = nx.shortest_path(graph, "A", "D", weight="weight")
print(sp)

#go through links. initial and final point. build node id with rounded x/y coordinates. add edge.
#comput weight
#link edge to feature/geometry

