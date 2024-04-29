from shapely.geometry import box
import geopandas as gpd
from datetime import datetime

poi_dataset = '/home/juju/geodata/gisco/healthcare_EU.gpkg'
OME_dataset = '/home/juju/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg'
#the network layer to validate
layer = "tn_road_link"


#define 50km partition
partition_size = 50000
x_part = 3950000
y_part = 2850000
extention_percentage = 0.3

def proceed():
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

    #get populated grid cells in 50km partition

    #for each grid cell, get 5 hospitals around - compute shortest path to nearest
    #OR
    #for each hospital, compute shortest path to cells around - or isochrones


proceed()

