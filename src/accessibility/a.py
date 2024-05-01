import geopandas as gpd
from math import ceil,isnan
from accessibility_grid import accessibility_grid

#TODO
#remove grid cells loading ?
#OSM
#tomtom

#bbox = [3700000, 2700000, 4200000, 3400000]
bbox = [4000000, 2800000, 4100000, 2900000]
grid_resolution = 1000
num_processors_to_use = 8
partition_size = 100000
extention_buffer = 30000
cell_id_fun = lambda x,y: "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))

#OME2

pois_loader = lambda bbox: gpd.read_file('/home/juju/geodata/gisco/healthcare_EU_3035.gpkg', bbox=bbox)
road_network_loader = lambda bbox: gpd.read_file('/home/juju/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg', layer="tn_road_link", bbox=bbox)
grid_resolution = 1000
out_csv_file = "/home/juju/gisco/grid_accessibility_quality/accessibility_grid_OME2.csv"

accessibility_grid(pois_loader,
                       road_network_loader,
                       bbox,
                       out_csv_file,
                       cell_id_fun=cell_id_fun,
                       grid_resolution=grid_resolution,
                       partition_size = partition_size,
                       extention_buffer = extention_buffer,
                       num_processors_to_use = num_processors_to_use)
