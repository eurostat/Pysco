from datetime import datetime
import numpy as np
from rtree import index
import pandas as pd

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.convert import parquet_grid_to_geotiff
from utils.featureutils import index_from_geo_fiona


#TODO check duration : 30" for 10000 cells : 8h30 for 10e6 cells
#TODO optimise
#TODO parallel
#TODO parquet to tiff


def compute_nearby_population(pop_dict_loader, nearby_population_parquet, bbox, resolution=1000, only_populated_cells=False, radius_m = 120000):

    # make extended bbox
    (xmin, ymin, xmax, ymax) = bbox
    extended_bbox = (xmin-radius_m, ymin-radius_m, xmax+radius_m, ymax+radius_m)

    print(datetime.now(), "Load land mass cell index")
    lm = pd.read_parquet("/home/juju/gisco/road_transport_performance/cells_land_mass.parquet")
    print(datetime.now(), lm.size, "land mass figures loaded")
    lm.set_index("GRD_ID", inplace=True)

    print(datetime.now(), "Load population figures")
    pop_dict = pop_dict_loader(extended_bbox)
    print(datetime.now(), len(pop_dict.keys()), "population figures loaded")

    print(datetime.now(), "prepare cells...")

    cells = []
    items = []
    i = 0
    for x in range(xmin, xmax, resolution):
        for y in range(ymin, ymax, resolution):
            items.append((i, (x,y,x,y), None))
            id = 'CRS3035RES' + str(resolution) + 'mN' + str(y) + 'E' + str(x)
            pop = pop_dict[id]
            lmi = lm.loc[id]['code'].item()
            cells.append( { "x":x, "y":y, "GRD_ID": id, "pop":pop, "lmi":lmi } )
            i += 1

    # build index
    spatial_index = index.Index(((i, box, obj) for i, box, obj in items))
    del items

    print(datetime.now(), "free memory")
    del pop_dict
    del lm

    print(datetime.now(), "compute indicator for each cell...")
    # only those in the bbox, not the extended bbox
    cells_to_compute = list(spatial_index.intersection(bbox))
    print(datetime.now(), len(cells_to_compute))

    out_id = []
    out_indic = []
    radius_m_s = radius_m * radius_m

    for i in cells_to_compute:
        c = cells[i]

        p = c["pop"]
        if only_populated_cells and (p is None or p<=0): continue

        x = c["x"]
        y = c["y"]

        # get close cells using spatial index
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
    print(datetime.now(), "save")
    df.to_parquet(nearby_population_parquet)
    df.to_csv(nearby_population_parquet+'.csv', index=False)

    print(datetime.now(), "Done.")







# bbox - set to None to compute on the entire space
bbox = (3700000, 2700000, 3800000, 2800000)

for year in ["2018", "2021"]:
    print(year)

    if year == "2021":
        pop_dict_loader = lambda bbox : index_from_geo_fiona("/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg", "GRD_ID", "T", bbox=bbox)
    else:
        pop_dict_loader = lambda bbox : index_from_geo_fiona("/home/juju/geodata/gisco/grids/grid_1km_point.gpkg", "GRD_ID", "TOT_P_2018", bbox=bbox)

    parquet_file = "/home/juju/gisco/road_transport_performance/nearby_population_"+year+".parquet"
    compute_nearby_population(
        pop_dict_loader,
        parquet_file,
        bbox=bbox,
        only_populated_cells=False
    )

    print("parquet to geotiff")
    parquet_grid_to_geotiff(
        [parquet_file],
        "/home/juju/gisco/road_transport_performance/nearby_population_"+year+".tiff",
        #bbox=bbox,
        #attributes=["POP_N_120"],
        #grid_id_field='GRD_ID',
        #tiff_nodata_value=-9999,
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
