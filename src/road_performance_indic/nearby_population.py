from datetime import datetime
import fiona
from rtree import index
import csv

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import index_from_geo_fiona



# bbox - set to None to compute on the entire space
bbox = (3750000, 2720000, 3960000, 2970000)

year = "2021"
nearby_population_csv = "/home/juju/gisco/road_transport_performance/nearby_population_"+year+".csv"





def compute_nearby_population(nearby_population_csv, only_populated_cells=False, bbox=None, radius_m = 120000):

    print(datetime.now(), "Load population figures...")
    pop_dict = index_from_geo_fiona("/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg", "GRD_ID", "T", bbox=bbox)
    print(datetime.now(), len(pop_dict.keys()), "figures loaded")

    print(datetime.now(), "Load grid...")
    gpkg = fiona.open("/home/juju/geodata/gisco/grids/grid_1km_point.gpkg", 'r', driver='GPKG')
    cells = list(gpkg.items(bbox=bbox))
    gpkg.close()

    print(datetime.now(), len(cells), "cells loaded")

    print(datetime.now(), "prepare cells...")

    cells_ = []
    items = []
    i = 0
    for c in cells:
        c = c[1]
        x, y = c['geometry']['coordinates']
        items.append((i, (x,y,x,y), None))
        id = c["properties"]["GRD_ID"]
        pop = pop_dict[id]
        cells_.append( { "x":x, "y":y, "GRD_ID": id, "pop":pop } )
        i += 1

    # build index
    spatial_index = index.Index(((i, box, obj) for i, box, obj in items))
    del items

    print(datetime.now(), "free memory")
    del pop_dict
    del cells
    cells = cells_

    # precompute
    radius_m_s = radius_m * radius_m

    print(datetime.now(), "compute indicator for each cell...")

    output = []
    for c in cells:

        p = c["pop"]
        if only_populated_cells and (p is None or p<=0): continue

        #print(c)

        x = c["x"]
        y = c["y"]

        #get close cells using spatial index
        close_cells = list(spatial_index.intersection((x-radius_m, y-radius_m, x+radius_m, y+radius_m)))

        #compute population total
        pop_tot = 0
        for i2 in close_cells:
            c2 = cells[i2]
            p2 = c2["pop"]
            if p2 is None or p2<=0: continue

            #TODO
            #check if same land mass

            #too far: skip
            dx = x-c2["x"]
            dy = y-c2["y"]
            if dx*dx+dy*dy > radius_m_s : continue

            #sum population
            pop_tot += p2

        #print(pop_tot)
        output.append( { "pop":pop_tot, "GRD_ID":c["GRD_ID"] } )


    print(datetime.now(), "free memory")
    del spatial_index
    del cells

    print(datetime.now(), "Save as CSV")
    file = open(nearby_population_csv, mode="w", newline="", encoding="utf-8")
    writer = csv.DictWriter(file, fieldnames=output[0].keys())
    writer.writeheader()
    writer.writerows(output)

    print(datetime.now(), "Done.")




compute_nearby_population(nearby_population_csv, bbox=bbox, only_populated_cells=True)





'''
#raster mode, with convolution

import rasterio
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import geotiff_mask_by_countries, circular_kernel_sum

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
