import geopandas as gpd
from accessibility.zzz_old_accessibility_grid import accessibility_grid

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.ome2utils import ome2_duration
from utils.osmutils import osm_duration

#TODO
#check data loading with fiona only. faster ? filter on loading ?

bbox = [3800000, 2900000, 4200000, 3300000]
#bbox = [4000000, 2800000, 4100000, 2900000]
#bbox = [4100000, 2810000, 4110000, 2820000]

partition_size = 100000
extention_buffer = 30000
num_processors_to_use = 6
cell_id_fun = lambda x,y: "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))
out_folder = "/home/juju/gisco/grid_accessibility_quality/"

pois_loader = lambda bbox: gpd.read_file('/home/juju/geodata/gisco/healthcare_EU_3035.gpkg', bbox=bbox)


for detailled in [True]:
    for grid_resolution in [100, 1000]:
        for case in ["OME2","tomtom","OSM"]:
            #detailled = True if case == "OSM" else False

            print("###############", case, grid_resolution, detailled)

            if(case == "tomtom"):
                accessibility_grid(pois_loader,
                                    lambda bbox: gpd.read_file('/home/juju/geodata/tomtom/2021/nw.gpkg', bbox=bbox),
                                    lambda feature, length : -1 if feature.KPH==0 else 1.1*length/feature.KPH*3.6,
                                    bbox,
                                    out_folder,
                                    "accessibility_grid_"+case+"_" + str(grid_resolution) + "_" + str(detailled),
                                    cell_id_fun=cell_id_fun,
                                    grid_resolution=grid_resolution,
                                    cell_network_max_distance = grid_resolution*3,
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
                                    cell_network_max_distance = grid_resolution*3,
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
                                    cell_network_max_distance = grid_resolution*3,
                                    partition_size = partition_size,
                                    extention_buffer = extention_buffer,
                                    detailled = detailled,
                                    num_processors_to_use = num_processors_to_use)
