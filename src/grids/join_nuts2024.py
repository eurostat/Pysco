
import geopandas as gpd
import sys
import os
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


distance = 1500 # get nuts regions within 1.5 km
nuts_version = "2024"
nuts = "/home/juju/geodata/gisco/NUTS_RG_100K_"+nuts_version+"_3035.gpkg"

print("load nuts regions")
nuts = gpd.read_file(nuts)
#print(len(nuts))

for res in ["50"]: # "100", "50", "20", "10", "5", "2", "1"]:

    grid_path = "/home/juju/geodata/gisco/grids/grid_"+res+"km_surf.gpkg"
    grid = gpd.read_file(grid_path)
    print(len(grid))

    for lev in ["3", "2", "1", "0"]:
        print(res+"km", "level", lev)
        nuts_lev = nuts[nuts['STAT_LEVL_CODE'] == int(lev)]
        #print(len(nuts_lev))

        # make spatial index
        sindex = nuts_lev.sindex

        # function that finds a cell nuts codes
        def fun(cell):
            geom = cell["geometry"].buffer(distance)
            approx_matches = sindex.intersection(geom.bounds)

            codes = []
            for index in approx_matches:
                row = nuts_lev.iloc[index]
                if not geom.intersects(row["geometry"]): continue
                codes.append(row["NUTS_ID"])

            codes = list(set(codes))
            codes.sort()
            codes = "-".join(codes)
            return(codes)

        # set cell nuts codes
        grid['NUTS' + nuts_version + "_" + lev] = grid.apply( fun, axis=1 )

    print("save", res, "km")
    if os.path.exists(grid_path): os.remove(grid_path)
    grid.to_file(grid_path, driver="GPKG")

