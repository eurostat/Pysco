import datetime
from rasterio.enums import Resampling
from pygridmap import gridtiler_raster
import numpy as np

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import resample_geotiff_aligned


path = "/home/juju/gisco/degurba/"
resolutions = [10000, 5000, 2000, 1000]

# resampling
'''
for resolution in resolutions:
    print(datetime.now(), "resampling", resolution)
    resample_geotiff_aligned(path + "GHS-DUG_GRID_L2.tif", path + "/out/"+str(resolution)+".tif", resolution, resampling=Resampling.mode, dtype=np.int8)
'''


# tiling
for resolution in resolutions:
    print(datetime.now(), "Tiling", resolution)

    # make folder for resolution
    folder_ = path+"out/"+str(resolution)+"/"
    if not os.path.exists(folder_): os.makedirs(folder_)

    # prepare dict for geotiff bands
    dict = {}
    for year in ["2024"]:
        dict["du" + year] = {"file":path + "/out/"+str(resolution)+".tif", "band":1}

    # launch tiling
    gridtiler_raster.tiling_raster(
        dict,
        folder_,
        crs="EPSG:3035",
        tile_size_cell = 512,
        format="csv",
        num_processors_to_use = 8,
        modif_fun = lambda v: int(v),
        )

