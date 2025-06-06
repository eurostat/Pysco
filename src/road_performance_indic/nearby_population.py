from datetime import datetime
import fiona
from rtree import index
import pandas as pd

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import index_from_geo_fiona

#TODO check duration
#TODO optimise
#TODO extend bbox
#TODO parallel
#TODO parquet to tiff



def compute_nearby_population(pop_dict_loader, nearby_population_parquet, only_populated_cells=False, bbox=None, radius_m = 120000):

    print(datetime.now(), "Load land mass cell index")
    lm = pd.read_parquet("/home/juju/gisco/road_transport_performance/cells_land_mass.parquet")
    lm.set_index("GRD_ID", inplace=True)
    print(datetime.now(), lm.size, "figures loaded")

    print(datetime.now(), "Load grid")
    gpkg = fiona.open("/home/juju/geodata/gisco/grids/grid_1km_point.gpkg", 'r', driver='GPKG')
    cells = list(gpkg.items(bbox=bbox))
    gpkg.close()

    print(datetime.now(), "Load population figures")
    pop_dict = pop_dict_loader(bbox)
    print(datetime.now(), len(pop_dict.keys()), "figures loaded")


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
        lmi = lm.loc[id]['code'].item()
        cells_.append( { "x":x, "y":y, "GRD_ID": id, "pop":pop, "lmi":lmi } )
        i += 1

    # build index
    spatial_index = index.Index(((i, box, obj) for i, box, obj in items))
    del items

    print(datetime.now(), "free memory")
    del pop_dict
    del lm
    del cells
    cells = cells_

    # precompute
    radius_m_s = radius_m * radius_m

    print(datetime.now(), "compute indicator for each cell...")

    out_id = []
    out_indic = []
    for c in cells:

        p = c["pop"]
        if only_populated_cells and (p is None or p<=0): continue

        x = c["x"]
        y = c["y"]

        #get close cells using spatial index
        close_cells = list(spatial_index.intersection((x-radius_m, y-radius_m, x+radius_m, y+radius_m)))

        #compute population total
        lmi = c['lmi']
        pop_tot = 0
        for i2 in close_cells:
            c2 = cells[i2]
            p2 = c2["pop"]
            if p2 is None or p2<=0: continue

            # check if same land mass index
            if lmi != c2['lmi']: continue

            # too far: skip
            dx = x-c2["x"]
            dy = y-c2["y"]
            if dx*dx+dy*dy > radius_m_s : continue

            #sum population
            pop_tot += p2

        #print(pop_tot)
        out_id.append(c["GRD_ID"])
        out_indic.append(round(pop_tot))


    print(datetime.now(), "free memory")
    del spatial_index
    del cells

    df = pd.DataFrame( { "GRD_ID": out_id, "POP_N_120": out_indic } )
    print(datetime.now(), "Save")
    df.to_parquet(nearby_population_parquet)
    df.to_csv(nearby_population_parquet+'.csv', index=False)

    print(datetime.now(), "Done.")







# bbox - set to None to compute on the entire space
bbox = (3750000, 2720000, 3760000, 2770000)

for year in ["2018", "2021"]:
    print(year)

    if year == "2021":
        pop_dict_loader = lambda bbox : index_from_geo_fiona("/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg", "GRD_ID", "T", bbox=bbox)
    else:
        pop_dict_loader = lambda bbox : index_from_geo_fiona("/home/juju/geodata/gisco/grids/grid_1km_point.gpkg", "GRD_ID", "TOT_P_2018", bbox=bbox)

    compute_nearby_population(
        pop_dict_loader,
        "/home/juju/gisco/road_transport_performance/nearby_population_"+year+".parquet",
        bbox=bbox,
        only_populated_cells=False
    )





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
