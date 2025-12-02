# prepare accessibility grid for gridviz mapping

from pygridmap import gridtiler_raster
import sys
import os
from rasterio.enums import Resampling
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.geotiff import resample_geotiff_aligned

aggregate = True
tiling = True

version_tag = "v2025_11"
services = ["education", "healthcare"]  #education healthcare
resolutions = [ 100000, 50000, 20000, 10000, 5000, 2000, 1000, 500, 200, 100 ]

f0 = "/home/juju/gisco/accessibility/"
folder = f0 + "gridviz/"
if not os.path.exists(folder): os.makedirs(folder)

folder_pop_tiff = "/home/juju/geodata/census/2021/aggregated_tiff/"


# aggregate at various resolutions - average
if aggregate:
    print(datetime.now(), "aggregate")
    for year in ["2023", "2020"]:
        for service in services:

            # it is better to resample all resolution from 100m one. Otherwise, we do averages of averages which may create some biais around places with many nodata pixels
            for resolution in resolutions:
                print(datetime.now(), service, year, resolution)
                resample_geotiff_aligned(f0 + "euro_access_"+service+"_"+year+"_100m_"+version_tag+".tif", folder+"euro_access_"+service+"_" + year+"_"+str(resolution) + "m_"+version_tag+".tif", resolution, Resampling.med)

            '''
            print(service, year, 1000)
            resample_geotiff_aligned(folder+"euro_access_"+service+"_"+year+"_500m.tif", folder+"euro_access_"+service+"_" + year+"_1000m.tif", 1000, Resampling.average)

            for resolution in [2000, 5000, 10000]:
                print(service, year, resolution)
                resample_geotiff_aligned(folder+"euro_access_"+service+"_" + year+"_1000m.tif", folder+"euro_access_"+service+"_" + year+"_"+str(resolution)+"m.tif", resolution, Resampling.average)

            for resolution in [20000, 50000, 100000]:
                print(service, year, resolution)
                resample_geotiff_aligned(folder+"euro_access_"+service+"_" + year+"_10000m.tif", folder+"euro_access_"+service+"_" + year+"_"+str(resolution)+"m.tif", resolution, Resampling.average)
            '''

if tiling:
    print(datetime.now(), "tiling")
    for resolution in resolutions:
        for service in services:

            print(datetime.now(), "Tiling", service, resolution)

            # make folder for resolution
            folder_ = folder+"tiles_"+service+"_"+version_tag+"/"+str(resolution)+"/"
            if not os.path.exists(folder_): os.makedirs(folder_)

            # prepare dict for geotiff bands
            dict = {}
            for year in ["2020", "2023"]:
                dict["dt_1_" + year] = {"file":folder+"euro_access_"+service+"_"+year+"_"+str(resolution)+"m_"+version_tag+".tif", "band":1}
                dict["dt_a3_" + year] = {"file":folder+"euro_access_"+service+"_"+year+"_"+str(resolution)+"m_"+version_tag+".tif", "band":2}
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

