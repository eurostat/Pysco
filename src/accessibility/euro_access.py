from math import floor
from accessiblity_grid_k_nearest_dijkstra import accessiblity_grid_k_nearest_dijkstra
import numpy as np

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import iter_features
from utils.convert import parquet_grid_to_geotiff
from utils.geotiff import geotiff_mask_by_countries, rename_geotiff_bands

from tomtom_utils import weight_function, direction_fun, is_not_snappable_fun, initial_node_level_fun, final_node_level_fun


# whole europe
bbox = [ 1000000, 500000, 6000000, 5500000 ]
#luxembourg
#bbox = [4030000, 2930000, 4060000, 2960000]
#greece
#bbox = [ 5000000, 1500000, 5500000, 2000000 ]


tile_file_size_m = 500000
clamp = lambda v:floor(v/tile_file_size_m)*tile_file_size_m
[xmin,ymin,xmax,ymax] = [clamp(v) for v in bbox]

grid_resolution = 100
detailled = True
out_folder = '/home/juju/gisco/accessibility/'

def cell_id_fun(x,y): return "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))
def duration_simplification_fun(x): return int(round(x))


for service in ["education", "healthcare"]:

    for year in ["2020","2023"]:

        print(year, service)

        # ouput folder
        out_folder_service = out_folder + "out_" + service + "_" + year + "/"
        if not os.path.exists(out_folder_service): os.makedirs(out_folder_service)


        tomtom_year = "2019" if year == "2020" else year
        def road_network_loader(bbox): return iter_features("/home/juju/geodata/tomtom/tomtom_"+tomtom_year+"12.gpkg", bbox=bbox)
        def pois_loader(bbox): return iter_features("/home/juju/geodata/gisco/basic_services/"+service+"_"+year+"_3035.gpkg", bbox=bbox, where="levels!='0'" if service=="education" else "")
        num_processors_to_use = 7 if service == "education" else 4

        # launch process for each tile file
        for x in range(xmin, xmax, tile_file_size_m):
            for y in range(ymin, ymax, tile_file_size_m):

                #output file
                out_file = out_folder_service + "euro_access_" + service + "_" + str(grid_resolution) + "m_" + str(x) + "_" + str(y) + ".parquet"

                #check if output file was already produced
                if os.path.isfile(out_file): continue

                print("Tile file", x, y)

                # build accessibility grid
                accessiblity_grid_k_nearest_dijkstra(
                    pois_loader = pois_loader,
                    road_network_loader = road_network_loader,
                    bbox = [x, y, x+tile_file_size_m, y+tile_file_size_m],
                    out_parquet_file= out_file,
                    k = 3,
                    weight_function = weight_function,
                    direction_fun = direction_fun,
                    is_not_snappable_fun = is_not_snappable_fun,
                    initial_node_level_fun = initial_node_level_fun,
                    final_node_level_fun = final_node_level_fun,
                    cell_id_fun = cell_id_fun,
                    grid_resolution= grid_resolution,
                    cell_network_max_distance= grid_resolution * 2,
                    partition_size = 125000,
                    extention_buffer = 20000 if service=="education" else 60000,
                    detailled = detailled,
                    densification_distance=grid_resolution,
                    duration_simplification_fun = duration_simplification_fun,
                    num_processors_to_use = num_processors_to_use,
                )

        # parquet to tiff

        # check if tiff file was already produced
        geotiff = out_folder + "euro_access_" + service + "_" + year + "_" + str(grid_resolution) + "m.tif"
        if os.path.isfile(geotiff):
            #print(out_file, "already produced")
            continue

        # get all parquet files in the output folder
        files = [os.path.join(out_folder_service, f) for f in os.listdir(out_folder_service) if f.endswith('.parquet')]
        if len(files)==0: continue

        print("transforming", len(files), "parquet files into tif for", service, year)
        parquet_grid_to_geotiff(
            files,
            geotiff,
            bbox = bbox,
            attributes=["duration_s_1", "duration_average_s_3"],
            parquet_nodata_values=[-1],
            dtype=np.int16,
            value_fun= lambda v:v if v<32767 else 32767, # np.int16(v),
            compress='deflate'
        )

        print("apply mask to force some countries to nodata")
        geotiff_mask_by_countries(
            geotiff,
            geotiff,
            gpkg = '/home/juju/geodata/gisco/CNTR_RG_100K_2024_3035.gpkg',
            gpkg_column = 'CNTR_ID',
            values_to_exclude = ["DE", "CH", "RS", "BA", "MK", "AL", "ME", "MD"],
            compress="deflate"
        )

        print("rename bands")
        rename_geotiff_bands(geotiff, [service + "_" + year + "_1", service + "_" + year + "_a3"])

