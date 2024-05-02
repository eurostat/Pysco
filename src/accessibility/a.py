import geopandas as gpd
from math import ceil,isnan
from accessibility_grid import accessibility_grid

import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from lib.ome2utils import ome2_duration

#TODO
#test with detailled network - new graph making function. merge graph_from_geodataframe_with_segments functions ?
#test with OSM
#compare
#tomtom

#bbox = [3700000, 2700000, 4200000, 3400000]
bbox = [4000000, 2800000, 4100000, 2900000]
grid_resolution = 1000
num_processors_to_use = 8
partition_size = 100000
extention_buffer = 30000
cell_id_fun = lambda x,y: "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))
detailled = False

out_folder = "/home/juju/gisco/grid_accessibility_quality/"

#set variables

#OME2
case = "OME2"
pois_loader = lambda bbox: gpd.read_file('/home/juju/geodata/gisco/healthcare_EU_3035.gpkg', bbox=bbox)
road_network_loader = lambda bbox: gpd.read_file('/home/juju/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg', layer="tn_road_link", bbox=bbox)
weight_function = lambda feature, length : ome2_duration(feature, length)

#OSM
#TODO

#execute accessibility analysis
accessibility_grid(pois_loader,
                       road_network_loader,
                       weight_function,
                       bbox,
                       out_folder,
                       "accessibility_grid_" + case + "_" + str(grid_resolution) + "_" + str(detailled),
                       cell_id_fun=cell_id_fun,
                       grid_resolution=grid_resolution,
                       partition_size = partition_size,
                       extention_buffer = extention_buffer,
                       detailled = detailled,
                       num_processors_to_use = num_processors_to_use)
