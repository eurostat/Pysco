from gridtiler import grid_tiling
from gridaggregator import grid_aggregation
from gridtransformation import grid_transformation


#set cell x,y from its grid_id
def position_fun(c):
    a = c['GRD_ID'].split("N")[1].split("E")
    c["x"] = int(a[1])
    c["y"] = int(a[0])
    del c['GRD_ID']


grid_transformation(
    "/home/juju/gisco/building_demography/building_demography.csv",
    position_fun,
    '/home/juju/Bureau/out_100.csv'
)


""""

grid_aggregation(
    "/home/juju/gisco/building_demography/building_demography.csv",
    100,
    '/home/juju/Bureau/out_1000.csv',
    10
)



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