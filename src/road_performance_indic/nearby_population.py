from datetime import datetime
import numpy as np
from rtree import index
import pandas as pd
from multiprocessing import Pool

import sys
import os

from utils.utils import cartesian_product_comp
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.convert import parquet_grid_to_geotiff #, parquet_grid_to_gpkg
from utils.featureutils import index_from_geo_fiona


#TODO parallel
#TODO check duration : 30" for 10000 cells : 8h30 for 10e6 cells


def __parallel_process(xy, partition_size, pop_dict_loader, land_mass_dict_loader, resolution=1000, only_populated_cells=False, radius_m = 120000):

    # make extended bbox
    [xmin, ymin] = xy
    xmax = xmin + partition_size
    ymax = ymin + partition_size
    extended_bbox = (xmin-radius_m-resolution, ymin-radius_m-resolution, xmax+radius_m+resolution, ymax+radius_m+resolution)

    print(datetime.now(),xmin, ymin, "Load land mass cell index")
    lm_dict = land_mass_dict_loader(extended_bbox)
    print(datetime.now(),xmin, ymin, len(lm_dict.keys()), "land mass figures loaded")

    print(datetime.now(),xmin, ymin, "Load population figures")
    pop_dict = pop_dict_loader(extended_bbox)
    print(datetime.now(),xmin, ymin, len(pop_dict.keys()), "population figures loaded")

    print(datetime.now(),xmin, ymin, "prepare cells...")

    cells = []
    items = []
    r2 = resolution/2
    i = 0
    for x in range(xmin-radius_m-resolution, xmax+radius_m+resolution, resolution):
        for y in range(ymin-radius_m-resolution, ymax+radius_m+resolution, resolution):
            id = 'CRS3035RES' + str(resolution) + 'mN' + str(y) + 'E' + str(x)
            p = pop_dict[id]
            if only_populated_cells and (p is None or p<=0): continue
            items.append((i, (x+r2,y+r2,x+r2,y+r2)))
            lmi = lm_dict[id]
            cells.append( { "x":x, "y":y, "GRD_ID": id, "pop":p, "lmi":lmi } )
            i += 1

    del pop_dict
    del lm_dict

    # build index
    spatial_index = index.Index(((i, box, None) for i, box in items))
    del items

    # compute indicator only for those in the bbox, not the extended bbox
    cells_to_compute = list(spatial_index.intersection( (xmin+resolution*0.1, ymin+r2, xmax-resolution*0.1, ymax-resolution*0.1) ))
    print(datetime.now(),xmin, ymin, len(cells_to_compute))

    print(datetime.now(),xmin, ymin, "compute indicator for each cell...")
    out_id = []
    out_indic = []
    radius_m_s = radius_m * radius_m
    rr = radius_m-resolution

    for i in cells_to_compute:
        c = cells[i]

        # get close cells using spatial index
        x = c["x"]; y = c["y"]
        close_cells = spatial_index.intersection( (x-rr, y-rr, x+rr, y+rr) )

        '''
        #compute population total
        pop_tot = 0
        lmi = c['lmi']
        for i2 in close_cells:
            c2 = cells[i2]

            p2 = c2["pop"]
            if p2 is None or p2<=0: continue

            # check if same land mass index
            if lmi != c2['lmi']: continue

            # too far: skip
            dx = x-c2["x"]
            dy = y-c2["y"]
            if dx*dx + dy*dy > radius_m_s : continue

            # sum population
            pop_tot += p2
        '''

        #TODO check if it is faster !
        pop_tot = sum(cells[i2]["pop"] for i2 in close_cells
                        if cells[i2]["pop"] and cells[i2]["lmi"] == lmi
                        and (x - cells[i2]["x"])**2 + (y - cells[i2]["y"])**2 <= radius_m_s)


        #print(pop_tot)
        out_id.append(c["GRD_ID"])
        out_indic.append(round(pop_tot))

    print(datetime.now(),xmin, ymin, "done -", len(cells))
    del spatial_index
    del cells

    return( [out_id, out_indic] )




def compute_nearby_population(pop_dict_loader,
                              land_mass_dict_loader,
                              bbox,
                              resolution=1000,
                              only_populated_cells=False,
                              radius_m = 120000,
                              partition_size = 100000,
                              num_processors_to_use = 1):

    processes_params = cartesian_product_comp(bbox[0], bbox[1], bbox[2], bbox[3], partition_size)
    processes_params = [
        ( xy, partition_size, pop_dict_loader, land_mass_dict_loader, resolution, only_populated_cells, radius_m )
        for xy in processes_params ]

    print(datetime.now(), "launch", len(processes_params), "processes on", num_processors_to_use, "processor(s)")
    outputs = Pool(num_processors_to_use).starmap(__parallel_process, processes_params)

    print(datetime.now(), "combine", len(outputs), "outputs")

    out_id = []
    out_indic = []
    for out in outputs:
        # skip if empty result
        if out==None : continue
        if len(out[0])==0: continue

        # combine results
        out_id += out[0]
        out_indic += out[1]

    print(datetime.now(), len(out_id), "cells")

    # save output
    print(datetime.now(), "save as parquet")
    df = pd.DataFrame( { "GRD_ID": out_id, "POP_N_120": out_indic } )
    df.to_parquet(parquet_file)





for year in ["2021", "2018"]:
    print(year)

    out_folder = "/home/juju/gisco/road_transport_performance/nearby_population_"+year+"/"
    if not os.path.exists(out_folder): os.makedirs(out_folder)

    if year == "2021":
        pop_dict_loader = lambda bbox : index_from_geo_fiona("/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg", "GRD_ID", "T", bbox=bbox)
    else:
        pop_dict_loader = lambda bbox : index_from_geo_fiona("/home/juju/geodata/gisco/grids/grid_1km_point.gpkg", "GRD_ID", "TOT_P_2018", bbox=bbox)

    lm_dict_loader = lambda bbox : index_from_geo_fiona("/home/juju/gisco/road_transport_performance/cells_land_mass.gpkg", "GRD_ID", "code", bbox=bbox)

    xy = [3900000, 2600000]
    partition_size = 100000

    res = __parallel_process(
        xy,
        partition_size,
        pop_dict_loader,
        lm_dict_loader,
        only_populated_cells=False,
        radius_m = 120000,
    )

    parquet_file = out_folder + "todo.parquet"
    [out_id, out_indic] = res
    df = pd.DataFrame( { "GRD_ID": out_id, "POP_N_120": out_indic } )
    df.to_parquet(parquet_file)
    #df.to_csv(parquet_file+'.csv', index=False)

    print(year, "parquet to geotiff")
    files = [os.path.join(out_folder, f) for f in os.listdir(out_folder) if f.endswith('.parquet')]
    if len(files)==0: continue
    parquet_grid_to_geotiff(
        files,
        "/home/juju/gisco/road_transport_performance/nearby_population_"+year+".tiff",
        dtype=np.int32,
        compress='deflate',
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
