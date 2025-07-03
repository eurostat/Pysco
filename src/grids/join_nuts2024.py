
import geopandas as gpd

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


nuts_version = "2024"
nuts = "/home/juju/geodata/gisco/NUTS_RG_100K_"+nuts_version+"_3035.gpkg"

print("load nuts regions")
nuts = gpd.read_file(nuts)
#print(len(nuts))

for res in ["100"]: #, "50", "20", "10", "5", "2", "1"]:

    grid_path = "/home/juju/geodata/gisco/grids/grid_"+res+"km_surf.gpkg"
    grid = gpd.read_file(grid_path)
    print(len(grid))

    for lev in ["3", "2", "1", "0"]:
        nuts_lev = nuts[nuts['STAT_LEVL_CODE'] == int(lev)]
        #print(len(nuts_lev))

    def fun(cell):
        return "TODO"
        #"NUTS_ID"

    grid['NUTS_'+nuts_version] = grid.apply(
        fun,
        axis=1
    )

    print("save", res, "km")
    if os.path.exists(grid_path): os.remove(grid_path)
    grid.to_file(f, driver="GPKG")

