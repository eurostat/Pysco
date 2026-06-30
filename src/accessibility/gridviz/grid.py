# prepare accessibility grid for gridviz map

from pygridmap import gridtiler_raster
import sys
import os
import shutil
from rasterio.enums import Resampling
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.geotiff import resample_geotiff_aligned
from accessibility.euro_access import out_folder, target_folder, dataset_versions

folder_pop_tiff = "/home/juju/geodata/census/2021/aggregated_tiff/"

aggregate = True
tiling = True
zip_move = True

get_k = lambda service: 5 if service == "evrp" else 3

resolutions = [ 100000, 50000, 20000, 10000, 5000, 2000, 1000, 500, 200, 100 ]

folder_gridviz = out_folder + "gridviz/"
if not os.path.exists(folder_gridviz): os.makedirs(folder_gridviz)

# aggregate at various resolutions - median
if aggregate:
    print(datetime.now(), "aggregate")
    for service in dataset_versions.keys():
        for year in dataset_versions[service].keys():

            # it is better to resample all resolution from 100m one. Otherwise, we do medians of medians which may create some biais around places with many nodata pixels
            for resolution in resolutions:
                print(datetime.now(), service, year, resolution)
                resample_geotiff_aligned(out_folder + "euro_access_"+service+"_"+year+"_100m_"+dataset_versions[service][year]+".tif",
                                         folder_gridviz+"euro_access_"+service+"_" + year+"_"+str(resolution) + "m_"+dataset_versions[service][year]+".tif",
                                         resolution, Resampling.med)


if tiling:
    print(datetime.now(), "tiling")
    for resolution in resolutions:
        for service in dataset_versions.keys():

            print(datetime.now(), "Tiling", service, resolution)

            # make folder for resolution
            folder_ = folder_gridviz + service + "/" + str(resolution) + "/"
            if not os.path.exists(folder_): os.makedirs(folder_)

            # prepare dict for geotiff bands
            dict = {}
            k = get_k(service)
            for year in dataset_versions[service].keys():
                dict["dt_1_" + year] = {"file":folder_gridviz+"euro_access_"+service+"_"+year+"_"+str(resolution)+"m_"+dataset_versions[service][year]+".tif", "band":1}
                dict["dt_a"+str(k)+"_" + year] = {"file":folder_gridviz+"euro_access_"+service+"_"+year+"_"+str(resolution)+"m_"+dataset_versions[service][year]+".tif", "band":2}
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
    # move/copy tiffs
    for service in dataset_versions.keys():

        # zip and move tiles
        print(datetime.now(), "Zip tiles", service)
        shutil.make_archive(folder_gridviz + service, "zip", folder_gridviz + service + "/")
        print(datetime.now(), "Move zip file", service)
        shutil.move(folder_gridviz + service + ".zip", target_folder)

        for year in dataset_versions[service].keys():
            print(datetime.now(), "Copy tiff files", service, year)

            # 100m
            shutil.copy(out_folder+"euro_access_"+service+"_"+year+"_100m_"+dataset_versions[service][year]+".tif", target_folder)
            # 1000m
            shutil.copy(folder_gridviz+"euro_access_"+service+"_"+year+"_1000m_"+dataset_versions[service][year]+".tif", out_folder)
            shutil.copy(out_folder+"euro_access_"+service+"_"+year+"_1000m_"+dataset_versions[service][year]+".tif", target_folder)
