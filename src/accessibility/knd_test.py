import geopandas as gpd
from shapely.geometry import box
from accessiblity_grid_k_nearest_dijkstra import graph_adjacency_list_from_geodataframe, multi_source_k_nearest_dijkstra, export_dijkstra_results_to_gpkg
from datetime import datetime
#import random

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.netutils import nodes_spatial_index_adjacendy_list


k=3
with_paths = False
nb_sources = 10

pois_loader = lambda bbox: gpd.read_file('/home/juju/geodata/gisco/basic_services/healthcare_2023_3035.gpkg', bbox=bbox)
road_network_loader = lambda bbox: gpd.read_file('/home/juju/geodata/tomtom/tomtom_202312.gpkg', bbox=bbox)
weight_function = lambda feature, length : -1 if feature.KPH==0 else 1.1*length/feature.KPH*3.6,

bbox = box(4034000, 2946000, 4053000, 2958000)
#extended_bbox = (4000000, 2500000, 4500000, 3000000)

#data = gpd.read_file(tomtom, bbox=bbox)
#print(len(data))

print(datetime.now(),"load POIs")
pois = pois_loader(bbox)
print(len(pois))

print(datetime.now(), "load road sections")
roads = road_network_loader(bbox)
print(len(roads))

print(datetime.now(), "make graph")
graph = graph_adjacency_list_from_geodataframe(roads)
del roads
print(len(graph.keys()), "nodes")

print(datetime.now(), "get source nodes")
idx = nodes_spatial_index_adjacendy_list(graph)
nodes_ = list(graph.keys())
sources = []
for iii, poi in pois.iterrows():
    n = nodes_[next(idx.nearest((poi.geometry.x, poi.geometry.y, poi.geometry.x, poi.geometry.y), 1))]
    sources.append(n)
del pois, nodes_, idx
print(len(sources))

print(datetime.now(), "compute accessiblity")
result = multi_source_k_nearest_dijkstra(graph=graph, k=k, sources=sources, with_paths=with_paths)
del graph

print(datetime.now(), "save outputs")
export_dijkstra_results_to_gpkg(result, "/home/juju/Bureau/output.gpkg", crs="EPSG:3035", k=k, with_paths=with_paths)

print(datetime.now(), "Done")

