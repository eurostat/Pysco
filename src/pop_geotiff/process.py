
import numpy as np
from rasterio.enums import Resampling

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import resample_geotiff_aligned

input_tiff = "/home/juju/geodata/jrc/JRC_CENSUS_2021_100m_grid/JRC-CENSUS_2021_100m_new_bbox.tif"
folder = "/home/juju/geodata/census/2021/aggregated_tiff"


# aggregate 
def aggregate_population():
    for f in [2, 5, 10]:
        resolution = 100 * f
        print("aggregate population", resolution)
        resample_geotiff_aligned(input_tiff, folder+"pop_2021_"+str(resolution)+".tif", resolution, Resampling.sum, dtype=np.int64)
    for f in [2, 5, 10]:
        resolution = 1000 * f
        print("aggregate population", resolution)
        resample_geotiff_aligned(folder+"pop_2021_1000.tif", folder+"pop_2021_"+str(resolution)+".tif", resolution, Resampling.sum, dtype=np.int64)
    for f in [2, 5, 10]:
        resolution = 10000 * f
        print("aggregate population", resolution)
        resample_geotiff_aligned(folder+"pop_2021_10000.tif", folder+"pop_2021_"+str(resolution)+".tif", resolution, Resampling.sum, dtype=np.int64)

