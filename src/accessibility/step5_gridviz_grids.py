# prepare accessibility grid for gridviz map

from pygridmap import gridtiler_raster
import os
import shutil
from datetime import datetime

def gridviz_tiling(params, services=None):

    if services is None: services = params["pois_datasets"].keys()
    get_k = lambda service: 5 if service == "evrp" else 3

    resolutions = [ 100000, 50000, 20000, 10000, 5000, 2000, 1000, 500, 200, 100 ]

    folder_aggregated = params["out_folder"] + "aggregated/"
    folder_gridviz = params["out_folder"] + "gridviz/"
    if not os.path.exists(folder_gridviz): os.makedirs(folder_gridviz)

    for service in services:
        for resolution in resolutions:

            print(datetime.now(), "Tiling", service, resolution)

            # make folder for resolution
            folder_ = folder_gridviz + service + "/" + str(resolution) + "/"
            if not os.path.exists(folder_): os.makedirs(folder_)

            # prepare dict for geotiff bands
            dict = {}
            k = get_k(service)
            for year in params["accessibility_grid_versions"][service].keys():
                dict["dt_1_" + year] = {"file":folder_aggregated+"euro_access_"+service+"_"+year+"_"+str(resolution)+"m_"+params["accessibility_grid_versions"][service][year]+".tif", "band":1}
                dict["dt_a"+str(k)+"_" + year] = {"file":folder_aggregated+"euro_access_"+service+"_"+year+"_"+str(resolution)+"m_"+params["accessibility_grid_versions"][service][year]+".tif", "band":2}
                dict["POP_2021"] = { "file":params["folder_pop_tiff"]+"pop_2021_"+str(resolution)+".tif", "band":1 }

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

    if "deploy_target_folder" in params:
        for service in services:
            # zip and move tiles
            print(datetime.now(), service, "Zip tiles")
            shutil.make_archive(folder_gridviz + service, "zip", folder_gridviz + service + "/")
            print(datetime.now(), service, "Move zip file")
            shutil.move(folder_gridviz + service + ".zip", params["deploy_target_folder"])

