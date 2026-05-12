# prepare accessibility grid for gridviz map

from pygridmap import gridtiler_raster
import sys
import os
import shutil
from rasterio.enums import Resampling
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.geotiff import resample_geotiff_aligned

folder = "/home/juju/gisco/accessibility/"
folder_pop_tiff = "/home/juju/geodata/census/2021/aggregated_tiff/"
target_folder = "/home/juju/pCloudDrive"

aggregate = True
tiling = True
zip_move = True

version_tag = "v2026_05"
services = ["evrp"]  # healthcare education evrp
resolutions = [ 100000, 50000, 20000, 10000, 5000, 2000, 1000, 500, 200, 100 ]
get_years = lambda service: ["2024", "2023"] if service == "evrp" else ["2023", "2020"]
get_k = lambda service: 5 if service == "evrp" else 3

folder_gridviz = folder + "gridviz/"
if not os.path.exists(folder_gridviz): os.makedirs(folder_gridviz)

# aggregate at various resolutions - median
if aggregate:
    print(datetime.now(), "aggregate")
    for service in services:
        for year in get_years(service):

            # it is better to resample all resolution from 100m one. Otherwise, we do medians of medians which may create some biais around places with many nodata pixels
            for resolution in resolutions:
                print(datetime.now(), service, year, resolution)
                resample_geotiff_aligned(folder + "euro_access_"+service+"_"+year+"_100m_"+version_tag+".tif",
                                         folder_gridviz+"euro_access_"+service+"_" + year+"_"+str(resolution) + "m_"+version_tag+".tif",
                                         resolution, Resampling.med)


if tiling:
    print(datetime.now(), "tiling")
    for resolution in resolutions:
        for service in services:

            print(datetime.now(), "Tiling", service, resolution)

            # make folder for resolution
            folder_ = folder_gridviz + service + "/" + str(resolution) + "/"
            if not os.path.exists(folder_): os.makedirs(folder_)

            # prepare dict for geotiff bands
            dict = {}
            k = get_k(service)
            for year in get_years(service):
                dict["dt_1_" + year] = {"file":folder_gridviz+"euro_access_"+service+"_"+year+"_"+str(resolution)+"m_"+version_tag+".tif", "band":1}
                dict["dt_a"+str(k)+"_" + year] = {"file":folder_gridviz+"euro_access_"+service+"_"+year+"_"+str(resolution)+"m_"+version_tag+".tif", "band":2}
                dict["POP_2021"] = { "file":folder_pop_tiff+"pop_2021_"+str(resolution)+".tif", "band":1 }

            # launch tiling
            gridtiler_raster.tiling_raster(
                dict,
                folder_,
                crs="EPSG:3035",
                tile_size_cell = 256,
                format="parquet",
                num_processors_to_use = 10,
                modif_fun = round,
                )
            
if zip_move:
    # zip and move tiles
    shutil.make_archive(folder_gridviz + service + ".zip", "zip", folder_gridviz + service + "/")
    shutil.move(folder_gridviz + service + ".zip", target_folder)

    # move/copy tiffs
    for service in services:
        for year in get_years(service):
            # 100m
            shutil.copy(folder+"euro_access_"+service+"_"+year+"_100m_"+version_tag+".tif", target_folder)
            # 1000m
            shutil.copy(folder_gridviz+"euro_access_"+service+"_"+year+"_1000m_"+version_tag+".tif", folder)
            shutil.copy(folder+"euro_access_"+service+"_"+year+"_1000m_"+version_tag+".tif", target_folder)
