import geopandas as gpd
from accessibility_grid import accessibility_grid

import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from utils.ome2utils import ome2_duration
from utils.osmutils import osm_duration

#TODO
#test with tomtom
#compare

#bbox = [3700000, 2700000, 4200000, 3400000]
bbox = [4000000, 2800000, 4100000, 2900000]
#bbox = [4100000, 2810000, 4110000, 2820000]

partition_size = 100000
extention_buffer = 30000
num_processors_to_use = 8
cell_id_fun = lambda x,y: "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))
out_folder = "/home/juju/gisco/grid_accessibility_quality/"

pois_loader = lambda bbox: gpd.read_file('/home/juju/geodata/gisco/healthcare_EU_3035.gpkg', bbox=bbox)


for detailled in [True]:
    for case in ["tomtom"]:
        for grid_resolution in [1000, 100]:

            print(case, grid_resolution, detailled)

            if(case == "tomtom"):
                accessibility_grid(pois_loader,
                                    lambda bbox: gpd.read_file('/home/juju/geodata/tomtom/2021/nw.gpkg', bbox=bbox),
                                    lambda feature, length : lambda feature, length : feature.MINUTES * 60
                                    bbox,
                                    out_folder,
                                    "accessibility_grid_"+case+"_" + str(grid_resolution) + "_" + str(detailled),
                                    cell_id_fun=cell_id_fun,
                                    grid_resolution=grid_resolution,
                                    partition_size = partition_size,
                                    extention_buffer = extention_buffer,
                                    detailled = detailled,
                                    num_processors_to_use = num_processors_to_use)

            if(case == "OME2"):
                accessibility_grid(pois_loader,
                                    lambda bbox: gpd.read_file('/home/juju/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg', layer="tn_road_link", bbox=bbox),
                                    lambda feature, length : ome2_duration(feature, length),
                                    bbox,
                                    out_folder,
                                    "accessibility_grid_"+case+"_" + str(grid_resolution) + "_" + str(detailled),
                                    cell_id_fun=cell_id_fun,
                                    grid_resolution=grid_resolution,
                                    partition_size = partition_size,
                                    extention_buffer = extention_buffer,
                                    detailled = detailled,
                                    num_processors_to_use = num_processors_to_use)

            elif(case == "OSM"):
                accessibility_grid(pois_loader,
                                    lambda bbox: gpd.read_file('/home/juju/geodata/OSM/europe_road_network_prep.gpkg', bbox=bbox),
                                    lambda feature, length : osm_duration(feature, length),
                                    bbox,
                                    out_folder,
                                    "accessibility_grid_"+case+"_" + str(grid_resolution) + "_" + str(detailled),
                                    cell_id_fun=cell_id_fun,
                                    grid_resolution=grid_resolution,
                                    partition_size = partition_size,
                                    extention_buffer = extention_buffer,
                                    detailled = detailled,
                                    num_processors_to_use = num_processors_to_use)
