
import geopandas as gpd

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import read_geotiff_pixels_as_dicts
from utils.gridutils import get_cell_id


for res in ["100", "50", "20", "10", "5", "2", "1"]:

    grid = "/home/juju/geodata/gisco/grids/grid_"+res+"km_surf.gpkg"
    pop_2021 = "/home/juju/geodata/census/2021/aggregated_tiff/pop_2021_"+res+"000.tif"

    print("load gpkg grid", res+"000m")
    gdf = gpd.read_file(grid)
    #print(gdf.head())
    #print(gdf['TOT_P_2021'].tolist())

    print("load tiff pop 2021", res+"000m")
    pop_data = read_geotiff_pixels_as_dicts(pop_2021)
    #print(pop_data)

    # get pop 2021 data
    pop = {}
    for d in pop_data:
        id = get_cell_id(res+"000", "3035", d["x"], d["y"])
        pop[id] = float(d["value"])
    del pop_data


    # set population to 0 everywhere
    gdf['TOT_P_2021'] = 0

    gdf['TOT_P_2021'] = gdf.apply(
        lambda row: pop.get(row['GRD_ID'], row['TOT_P_2021']),
        axis=1
    )

    print("save", res)
    f = "/home/juju/geodata/gisco/grids/grid_"+res+"km_surf.gpkg"
    os.remove(f)
    gdf.to_file(f, driver="GPKG")

