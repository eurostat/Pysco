import rasterio

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import geotiff_mask_by_countries, circular_kernel_sum



'''
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

for year in ["2018", "2021"]:
    print("convolution", year)
    circular_kernel_sum(
        "/home/juju/gisco/road_transport_performance/pop_"+year+".tiff",
        "/home/juju/gisco/road_transport_performance/nearby_population_"+year+".tiff",
        120000,
        rasterio.uint32,
        compress="deflate",
        )







'''
import rasterio
import numpy as np
from scipy import ndimage




def circular_kernel_sum(
    input_tiff,
    output_tiff,
    radius_m = 120000,
    dtype=rasterio.float32,
    compress=None,
):

    #print("open the input GeoTIFF")
    with rasterio.open(input_tiff) as src:
        data = src.read(1)
        profile = src.profile
        nodata = src.nodata
        pixel_size = src.res[0]  # assuming square pixels

    #print("replace data")

    # Replace nodata with 0 for computation
    if nodata is not None:
        data = np.where(data == nodata, 0, data)

    # Replace nodata and negative values with 0 for computation
    if nodata is not None:
        data = np.where((data == nodata) | (data < 0), 0, data)
    else:
        data = np.clip(data, 0, None)

    #print("change dtype")
    data = data.astype(dtype)

    #print("make circular kernel")
    radius_px = int(radius_m / pixel_size)
    y, x = np.ogrid[-radius_px:radius_px+1, -radius_px:radius_px+1]
    mask = x**2 + y**2 <= radius_px**2
    kernel = np.zeros((2*radius_px+1, 2*radius_px+1))
    kernel[mask] = 1

    #print("compute convolution using the kernel")
    data = ndimage.convolve(data, kernel, mode='constant', cval=0)

    #print("save")
    profile.update(dtype=dtype)
    if compress is not None: profile.update(compress=compress)

    with rasterio.open(output_tiff, "w", **profile) as dst:
        dst.write(data, 1)
'''






#import geopandas as gpd
#from datetime import datetime
#import concurrent.futures
#import threading
#import fiona
#from shapely.geometry import shape
#from rtree import index
#import csv


'''
# bbox - set to None to compute on the entire space
bbox = None #(3750000, 2720000, 3960000, 2970000)

# population grid
population_grid = "/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg"

# output CSV
nearby_population_csv = "/home/juju/gisco/road_transport_performance/nearby_population_2021.csv"




def compute_nearby_population(population_grid, layer, nearby_population_csv, only_populated_cells=True, bbox=None, radius_m = 120000):

    print(datetime.now(), "Load population grid...", population_grid)
    gpkg = fiona.open(population_grid, 'r', driver='GPKG')
    where = "T > 0" if only_populated_cells else None
    cells = list(gpkg.items(bbox=bbox, layer=layer, where=where))
    gpkg.close()

    print(datetime.now(), len(cells), "cells loaded")

    print(datetime.now(), "prepare cells...")
    spatial_index = index.Index()
    cells_ = []

    # feed index
    i = 0
    for c in cells:
        c = c[1]
        geom = shape(c["geometry"])
        pt = geom.centroid
        spatial_index.insert(i, geom.bounds)
        cells_.append( {"pop":c["properties"]["T"], "x":pt.x, "y":pt.y, "GRD_ID": c["properties"]["GRD_ID"]} )
        i += 1

    print(datetime.now(), "free memory")
    del cells
    cells = cells_

    #precompute
    radius_m_s = radius_m * radius_m

    print(datetime.now(), "compute indicator for each cell...")

    #lock = threading.Lock()
    def compute_cell(c):
        x=c["x"]
        y=c["y"]

        #get close cells using spatial index
        #close_cells = None
        #with lock:
        close_cells = list(spatial_index.intersection((x-radius_m, y-radius_m, x+radius_m, y+radius_m)))

        #compute population total
        pop_tot = 0
        for i2 in close_cells:
            c2 = cells[i2]
            dx = x-c2["x"]
            dy = y-c2["y"]

            #too far: skip
            if dx*dx+dy*dy>radius_m_s :continue

            #sum population
            pop_tot += c2["pop"]

        return { "pop":pop_tot, "GRD_ID":c["GRD_ID"] }

    #compute, not in parallel
    output = []
    for c in cells: output.append( compute_cell(c) )

    # Run in parallel
    #executor = concurrent.futures.ThreadPoolExecutor()
    #output = list(executor.map(compute_cell_indicator, cells))

    print(datetime.now(), "free memory")
    del spatial_index
    del cells

    print(datetime.now(), "Save as CSV")
    file = open(nearby_population_csv, mode="w", newline="", encoding="utf-8")
    writer = csv.DictWriter(file, fieldnames=output[0].keys())
    writer.writeheader()
    writer.writerows(output)

    print(datetime.now(), "Done.")




#
compute_nearby_population(population_grid, "census2021", nearby_population_csv, bbox=bbox)

'''
