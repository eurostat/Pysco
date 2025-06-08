# compute nearby population from raster data, using (fast) convolution

import numpy as np
import rasterio
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import geotiff_mask_by_countries, circular_kernel_sum, rasterise_tesselation_gpkg

'''
# prepare population grids

print("mask", "2018")
geotiff_mask_by_countries(
    "/home/juju/geodata/census/2018/JRC_1K_POP_2018_clean.tif",
    "/home/juju/gisco/road_transport_performance/pop_2018.tiff",
    gpkg = '/home/juju/geodata/gisco/CNTR_RG_100K_2024_3035.gpkg',
    gpkg_column = 'CNTR_ID',
    values_to_exclude = ["UK", "RS", "BA", "MK", "AL", "ME"],
    compress="deflate"
)
print("mask", "2021")
geotiff_mask_by_countries(
    "/home/juju/geodata/census/2021/ESTAT_OBS-VALUE-T_2021_V2_clean.tiff",
    "/home/juju/gisco/road_transport_performance/pop_2021.tiff",
    gpkg = '/home/juju/geodata/gisco/CNTR_RG_100K_2024_3035.gpkg',
    gpkg_column = 'CNTR_ID',
    values_to_exclude = ["UK", "RS", "BA", "MK", "AL", "ME"],
    compress="deflate"
)
'''

# apply fast convolution - without taking into account land mass index

for year in ["2018", "2021"]:
    print("convolution", year)
    circular_kernel_sum(
        "/home/juju/gisco/road_transport_performance/pop_"+year+".tiff",
        "/home/juju/gisco/road_transport_performance/nearby_population_"+year+"_fast.tiff",
        120000,
        rasterio.uint32,
        compress="deflate",
        )


resolution = 1000
year = 2021


# rasterise land mass index
rasterise_tesselation_gpkg(
    "/home/juju/gisco/road_transport_performance/land_mass_gridded.gpkg",
    "/home/juju/gisco/road_transport_performance/land_mass_gridded.tiff",
    fieldname='code',
    resolution=resolution,
    compression='deflate',
    nodata_value=-9999,
    dtype=np.int32
)




# combine with population

# compute convolution
