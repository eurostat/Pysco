#import geopandas as gpd
from accessibility.accessiblity_grid_k_nearest_dijkstra import build_graph_from_gpkg, multi_source_k_nearest_dijkstra, export_dijkstra_results_to_gpkg
from datetime import datetime
import random

k=3
with_paths = False
nb_sources = 100

tomtom = "/home/juju/geodata/tomtom/tomtom_202312.gpkg"
#bbox = (4034000, 2946000, 4053000, 2958000)
bbox = (4000000, 2500000, 4500000, 3000000)

#data = gpd.read_file(tomtom, bbox=bbox)
#print(len(data))


print(datetime.now(), "make graph")
graph = build_graph_from_gpkg(tomtom, "nw", bbox)
#print(graph)

print(datetime.now(), "select sources, as random nodes")
nodids = list(graph.keys())
sources = random.sample(nodids, nb_sources)

print(datetime.now(), "compute accessiblity")
result = multi_source_k_nearest_dijkstra(graph=graph, k=k, sources=sources, with_paths=with_paths)
del graph

print(datetime.now(), "save outputs")
export_dijkstra_results_to_gpkg(result, "/home/juju/Bureau/output.gpkg", crs="EPSG:3035", k=k, with_paths=with_paths)

print(datetime.now(), "Done")

