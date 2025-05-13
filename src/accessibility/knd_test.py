#import geopandas as gpd
from k_nearest_dijkstra import build_graph_from_gpkg, multi_source_k_nearest_dijkstra
from datetime import datetime
import random



tomtom = "/home/juju/geodata/tomtom/tomtom_202312.gpkg"
bbox = (4034000, 2946000, 4053000, 2958000)

#data = gpd.read_file(tomtom, bbox=bbox)
#print(len(data))


print(datetime.now(), "make graph")
graph = build_graph_from_gpkg(tomtom, "nw", bbox)
#print(graph)

nodids = graph.keys()
sources = random.sample(nodids, 30)
print(sources)


exit()

print(datetime.now(), "compute accessiblity")
out = multi_source_k_nearest_dijkstra(graph=graph, k=3, sources=sources, with_paths=False)

print(datetime.now(), "Done")

