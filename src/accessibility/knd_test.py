#import geopandas as gpd
from k_nearest_dijkstra import build_graph_from_gpkg
from datetime import datetime



tomtom = "/home/juju/geodata/tomtom/tomtom_202312.gpkg"
bbox = (4033580, 2945950, 4053279, 2958000)

#data = gpd.read_file(tomtom, bbox=bbox)
#print(len(data))


print(datetime.now(), "make graph")
graph = build_graph_from_gpkg(tomtom, "nw", bbox)
#print(graph)

print(datetime.now(), "Done")

