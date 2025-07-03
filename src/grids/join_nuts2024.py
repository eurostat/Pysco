# compute nuts_id field of grid cells
# the nuts dataset is gridified
# for each cell, the nuts patches within 1.5km are selected and a list of their codes is assigned to the grid cell.


import geopandas as gpd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.gridutils import gridify_gpkg


'''
# gridify nuts datasets
for nuts_version in ["2024", "2021", "2016"]:
    nuts = "/home/juju/geodata/gisco/NUTS_RG_100K_"+nuts_version+"_3035.gpkg"
    nuts_gridified = "/home/juju/geodata/gisco/grids/temp/nuts_gridified_"+nuts_version+".gpkg"

    print("gridifiy nuts", nuts_version)
    gridify_gpkg(nuts, 50000, nuts_gridified)
'''


distance = 1500 # get nuts regions within 1.5 km


nuts_data = {}
for nuts_version in ["2024", "2021", "2016"]:
    print("load nuts regions", nuts_version)

    nuts_gridified = "/home/juju/geodata/gisco/grids/temp/nuts_gridified_"+nuts_version+".gpkg"
    nuts_data[nuts_version] = gpd.read_file(nuts_gridified)



for res in ["100", "50", "20", "10", "5", "2", "1"]:

    grid_path = "/home/juju/geodata/gisco/grids/grid_"+res+"km_surf.gpkg"
    grid = gpd.read_file(grid_path)
    #print(len(grid))

    for nuts_version in ["2024", "2021", "2016"]:

        for lev in ["3", "2", "1", "0"]:
            print(res+"km", nuts_version, "level", lev)
            nuts = nuts_data[nuts_version]
            nuts_lev = nuts[nuts['STAT_LEVL_CODE'] == int(lev)]
            #print(len(nuts_lev))

            # make spatial index
            sindex = nuts_lev.sindex

            # function that finds a cell nuts codes
            def fun(cell):
                geom = cell["geometry"]
                if distance: geom = geom.buffer(distance)
                approx_matches = sindex.intersection(geom.bounds)

                codes = []
                for index in approx_matches:
                    row = nuts_lev.iloc[index]
                    if distance and not geom.intersects(row["geometry"]): continue
                    codes.append(row["NUTS_ID"])

                codes = list(set(codes))
                codes.sort()
                codes = "-".join(codes)
                return(codes)

            # set cell nuts codes
            grid['NUTS' + nuts_version + "_" + lev] = grid.apply( fun, axis=1 )

    print(res+"km", "save")
    if os.path.exists(grid_path): os.remove(grid_path)
    grid.to_file(grid_path, driver="GPKG")

