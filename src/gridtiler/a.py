from gridtiler import grid_tiling
from gridaggregator import grid_aggregation



grid_aggregation(
    "/home/juju/gisco/building_demography/building_demography.csv",
    100,
    '/home/juju/Bureau/out_1000.csv',
    10
)




""""

#set cell x,y from its grid_id
def position_fun(c):
    a = c['GRD_ID'].split("N")[1].split("E")
    c["x"] = int(a[1])
    c["y"] = int(a[0])
    del c['GRD_ID']


grid_tiling(
    "/home/juju/gisco/building_demography/building_demography.csv",
    '/home/juju/Bureau/test_tiling',
    100,
    #tile_size_cell = 128,
    x_origin = 2500000,
    y_origin = 1000000,
    crs = "EPSG:3035",
    preprocess = position_fun
)
"""