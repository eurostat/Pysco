from shapely.geometry import box
import geopandas as gpd
from datetime import datetime
import networkx as nx

import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from lib.netutils import shortest_path_geometry,graph_from_geodataframe,nodes_spatial_index,a_star_euclidian_dist



poi_dataset = '/home/juju/geodata/gisco/healthcare_EU_3035.gpkg'
OME_dataset = '/home/juju/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg'
pop_grid_dataset = '/home/juju/geodata/grids/grid_1km_surf.gpkg'
#the network layer to validate
layer = "tn_road_link"



#define 50km partition
x_part = 3950000
y_part = 2850000
partition_size = 10000
extention_percentage = 0.3




def proceed(x_part, y_part, partition_size):
    bbox = box(x_part, y_part, x_part+partition_size, y_part+partition_size)
    #make extended bbox around partition
    extended_bbox = box(x_part-partition_size*extention_percentage, y_part-partition_size*extention_percentage, x_part+partition_size*(1+extention_percentage), y_part+partition_size*(1+extention_percentage))

    print(datetime.now(), "load and filter network links")
    links = gpd.read_file(OME_dataset, layer=layer, bbox=extended_bbox)
    print(len(links))
    if(len(links)==0): return
    #rn = ome2_filter_road_links(links)
    #print(len(links))
    #if(len(links)==0): continue

    print(datetime.now(), "load and filter pois")
    pois = gpd.read_file(poi_dataset, bbox=extended_bbox)
    print(len(pois))
    if(len(pois)==0): return

    print(datetime.now(), "load population grid")
    pop = gpd.read_file(pop_grid_dataset, bbox=bbox)
    print(len(pop))
    if(len(pop)==0): return

    print(datetime.now(), "make graph")
    graph = graph_from_geodataframe(links)
    del rn

    #make list of nodes
    nodes_ = []
    for node in graph.nodes(): nodes_.append(node)

    #make nodes spatial index
    idx = nodes_spatial_index(graph)


    #snap hospitals to network


    #for each grid cell, get 5 hospitals around - compute shortest path to nearest
    #OR
    #for each hospital, compute shortest path to cells around - or isochrones


proceed(x_part, y_part, partition_size)

