
import geopandas as gpd

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))



nuts = "/home/juju/geodata/gisco/NUTS_RG_100K_2024_3035.gpkg"

print("load nuts regions")
nuts = gpd.read_file(nuts)
#print(len(nuts))

for res in ["100"]: #, "50", "20", "10", "5", "2", "1"]:

    grid = "/home/juju/geodata/gisco/grids/grid_"+res+"km_surf.gpkg"
    grid = gpd.read_file(grid)
    print(len(grid))


    for lev in ["3", "2", "1", "0"]:
        nuts_lev = nuts[nuts['STAT_LEVL_CODE'] == int(lev)]
        #print(len(nuts_lev))

        #"NUTS_ID"


