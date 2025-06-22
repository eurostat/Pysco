
import numpy as np
from rasterio.enums import Resampling

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import resample_geotiff_aligned

input_tiff_2018 = "/home/juju/geodata/census/2018/JRC_1K_POP_2018_clean_new_bbox.tif"
input_tiff_2021 = "/home/juju/geodata/jrc/JRC_CENSUS_2021_100m_grid/JRC-CENSUS_2021_100m_new_bbox.tif"
folder = "/home/juju/geodata/census/2021/aggregated_tiff"

def aggregate_population_2021():
    year = "2021"
    for f in [1, 2, 5, 10]:
        resolution = 100 * f
        print("aggregate population", resolution)
        resample_geotiff_aligned(input_tiff_2021, folder+"pop_"+year+"_"+str(resolution)+".tif", resolution, Resampling.sum, dtype=np.int64)
    for f in [2, 5, 10]:
        resolution = 1000 * f
        print("aggregate population", resolution)
        resample_geotiff_aligned(folder+"pop_"+year+"_1000.tif", folder+"pop_"+year+"_"+str(resolution)+".tif", resolution, Resampling.sum, dtype=np.int64)
    for f in [2, 5, 10]:
        resolution = 10000 * f
        print("aggregate population", resolution)
        resample_geotiff_aligned(folder+"pop_"+year+"_10000.tif", folder+"pop_"+year+"_"+str(resolution)+".tif", resolution, Resampling.sum, dtype=np.int64)


def aggregate_population_2018():
    year = "2018"
    for f in [1, 2, 5, 10]:
        resolution = 1000 * f
        print("aggregate population", resolution)
        resample_geotiff_aligned(folder+"pop_"+year+"_1000.tif", folder+"pop_"+year+"_"+str(resolution)+".tif", resolution, Resampling.sum, dtype=np.int64)
    for f in [2, 5, 10]:
        resolution = 10000 * f
        print("aggregate population", resolution)
        resample_geotiff_aligned(folder+"pop_"+year+"_10000.tif", folder+"pop_"+year+"_"+str(resolution)+".tif", resolution, Resampling.sum, dtype=np.int64)




print("aggregate population")
#aggregate_population_2021()
aggregate_population_2018()

