# prepare JRC 100m population grid for gridviz mapping

from pygridmap import gridtiler_raster
import sys
import os
from rasterio.enums import Resampling
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.geotiff import resample_geotiff_aligned

resolutions = [ 100000, 50000, 20000, 10000, 5000, 2000, 1000 ]

input_file = "/home/juju/geodata/jrc/JRC-CENSUS_DWELLINGS_2021_1km./JRC-CENSUS_DWELLINGS_2021_1km.tif"

# output folder
folder_out = "tmp/JRC_dwellings/"
os.makedirs(folder_out, exist_ok=True)

if False:
    for resolution in resolutions:
        print(datetime.now(), "Aggregate", resolution)
        resample_geotiff_aligned(input_file, folder_out+str(resolution)+".tif", resolution, Resampling.med)

if True:
    for resolution in resolutions:

        print(datetime.now(), "Tiling", resolution)

        # make folder for resolution
        folder_res = folder_out + str(resolution) + "/"
        os.makedirs(folder_res, exist_ok=True)

        # prepare dict for geotiff bands
        dict = {
            "D": { "file":folder_out+str(resolution)+".tif", "band":1, "no_data_values": [0, None, -9999] },
            "T": { "file":"/home/juju/geodata/census/2021/aggregated_tiff/pop_2021_"+str(resolution)+".tif", "band":1, "no_data_values": [0, None, -9999] }
        }

        # launch tiling
        gridtiler_raster.tiling_raster(
            dict,
            folder_res,
            crs="EPSG:3035",
            tile_size_cell = 512,
            format="parquet",
            num_processors_to_use = 10,
            modif_fun = round,
            )

