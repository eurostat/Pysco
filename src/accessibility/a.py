import geopandas as gpd
from math import ceil,isnan
from accessibility_grid import accessibility_grid


#TODO filter by country
#TODO do for osm


poi_dataset = '/home/juju/geodata/gisco/healthcare_EU_3035.gpkg'
OME_dataset = '/home/juju/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg'
pop_grid_dataset = '/home/juju/geodata/grids/grid_1km_surf.gpkg'
grid_resolution = 1000
#the network layer to validate
layer = "tn_road_link"

out_folder = "/home/juju/gisco/grid_accessibility_quality/"
out_file = "out"


bbox = [3700000, 2700000, 4200000, 3400000]
#bbox = [4000000, 2800000, 4100000, 2900000]
num_processors_to_use = 8
partition_size = 100000
extention_buffer = 30000 #on each side

