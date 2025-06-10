from shapely.geometry import box,Polygon
import geopandas as gpd
from datetime import datetime
import networkx as nx
#import concurrent.futures
#import threading
import fiona
import fiona.transform
from shapely.geometry import shape, mapping
from rtree import index
import csv

from utils.netutils import ___graph_adjacency_list_from_geodataframe, nodes_spatial_index_adjacendy_list
from utils.tomtomutils import direction_fun, final_node_level_fun, initial_node_level_fun, is_not_snappable_fun, weight_function
#from utils.featureutils import loadFeatures


#TODO
# Floyd-Warshall algorithm ?
# exclude ferry links



# bbox
[ x_part, y_part ] = [3750000, 2720000]
partition_size = 10000
show_detailled_messages =True
grid_resolution = 1000

# population grid
population_grid = "/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg"

# tomtom road network
tomtom = "/home/juju/geodata/tomtom/tomtom_202312.gpkg"
road_network_loader = lambda bbox: gpd.read_file('/home/juju/geodata/tomtom/2021/nw.gpkg', 'r', driver='GPKG', bbox=bbox),

# output CSV
accessible_population_csv = "/home/juju/gisco/road_transport_performance/accessible_population_2021.csv"


extention_buffer = 200000
# build partition extended bbox
extended_bbox = (x_part-extention_buffer, y_part-extention_buffer, x_part+partition_size+extention_buffer, y_part+partition_size+extention_buffer)


if show_detailled_messages: print(datetime.now(),x_part,y_part, "make graph")
roads = road_network_loader(extended_bbox)
gb_ = ___graph_adjacency_list_from_geodataframe(roads,
                                                    weight_fun = weight_function,
                                                    direction_fun = direction_fun,
                                                    is_not_snappable_fun = is_not_snappable_fun,
                                                    detailled = False,
                                                    densification_distance = grid_resolution,
                                                    initial_node_level_fun = initial_node_level_fun,
                                                    final_node_level_fun = final_node_level_fun)
graph = gb_['graph']
snappable_nodes = gb_['snappable_nodes']
del gb_, roads
if show_detailled_messages: print(datetime.now(),x_part,y_part, len(graph.keys()), "nodes,", len(snappable_nodes), "snappable nodes.")
#if(len(snappable_nodes)==0): return #TODO add that
#if(len(graph.keys())==0): return

if show_detailled_messages: print(datetime.now(),x_part,y_part, "build nodes spatial index")
idx = nodes_spatial_index_adjacendy_list(snappable_nodes)

