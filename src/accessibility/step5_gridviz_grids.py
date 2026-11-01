# prepare accessibility grid for gridviz map

from pygridmap import gridtiler_raster
import os
import shutil
from datetime import datetime

def gridviz_tiling(params, services=None):

    if services is None: services = params["pois_datasets"].keys()

    resolutions = [ 100000, 50000, 20000, 10000, 5000, 2000, 1000, 500, 200, 100 ]

    folder_aggregated = params["out_folder"] + "aggregated/"
    folder_gridviz = params["out_folder"] + "gridviz/"
    if not os.path.exists(folder_gridviz): os.makedirs(folder_gridviz)

    for service in services:
        for mode in params["modes"][service]:

            for ai in params["access_indicator"][service]:

                for resolution in resolutions:

                    folder_ = folder_gridviz + service + "_" + mode + "_" + ai + "/" + str(resolution) + "/"

                    # skip if already there
                    if os.path.exists(folder_):
                        continue

                    print(datetime.now(), "Tiling", service, mode, ai, resolution)

                    # make folder
                    os.makedirs(folder_)

                    # prepare dict for geotiff bands
                    dict = {}
                    band = 1 if ai == "N1" else 2
                    for year in params["accessibility_grid_versions"][service].keys():
                        dict["dt_" + ai + "_" + year] = {"file":folder_aggregated+"euro_access_"+service+"_"+year+"_"+mode+"_"+str(resolution)+"m_"+params["accessibility_grid_versions"][service][year]+".tif", "band":band}
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

                # zip and move tiles
                if "deploy_target_folder" in params:
                    f = folder_gridviz + service + "_" + mode
                    if os.path.exists(f+".zip"): continue

                    print(datetime.now(), service, mode, "Zip tiles")

                    shutil.make_archive(f, "zip", f + "/")

                    print(datetime.now(), service, mode, "Move zip file")
                    shutil.move(f + ".zip", params["deploy_target_folder"])

