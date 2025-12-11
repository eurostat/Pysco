# prepare JRC 100m population grid for gridviz mapping

from pygridmap import gridtiler_raster
import sys
import os
from rasterio.enums import Resampling
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.geotiff import resample_geotiff_aligned

tiling = True

resolutions = [ 100000, 50000, 20000, 10000, 5000, 2000, 1000, 500, 200, 100 ]

folder_pop_tiff = "/home/juju/geodata/census/2021/aggregated_tiff/"


if tiling:
    print(datetime.now(), "tiling")
    for resolution in resolutions:

        print(datetime.now(), "Tiling", resolution)

        # make folder for resolution
        folder_ = "tmp/JRC_100m/tiles_"+str(resolution)+"/"
        if not os.path.exists(folder_): os.makedirs(folder_)

        # prepare dict for geotiff bands
        dict = {
            "POP_2021": { "file":folder_pop_tiff+"pop_2021_"+str(resolution)+".tif", "band":1 }
        }

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

