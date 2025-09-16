from datetime import datetime
from rasterio.enums import Resampling
from pygridmap import gridtiler_raster
import numpy as np

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import resample_geotiff_aligned

path = "/home/juju/geodata/gisco/degurba/"
years = [ "2021", "2011" ]
resolutions = [10000, 5000, 2000, 1000]
resampling = True
tiling = False

# resampling
if resampling:
    for resolution in resolutions:
        for year in years:
            print(datetime.now(), "resampling", year, resolution)
            resample_geotiff_aligned(path + "GHS-DUG_GRID_L2_"+year+".tif", "./tmp/degurba/"+year+"_"+str(resolution)+".tif", resolution, resampling=Resampling.mode, dtype=np.int8)


# tiling
# TODO modify gridtiler to ignore value=10 (water) ?
if tiling:
    for resolution in resolutions:
        print(datetime.now(), "Tiling", resolution)

        # make folder for resolution
        folder_ = "./tmp/degurba/"+str(resolution)+"/"
        if not os.path.exists(folder_): os.makedirs(folder_)

        # prepare dict for geotiff bands
        dict = {}
        for year in years:
            dict["du" + year] = { "file" : "./tmp/degurba/"+year+"_"+str(resolution)+".tif", "band":1 }

        # launch tiling
        gridtiler_raster.tiling_raster(
            dict,
            folder_,
            crs="EPSG:3035",
            tile_size_cell = 512,
            format="parquet",
            num_processors_to_use = 8,
            )

