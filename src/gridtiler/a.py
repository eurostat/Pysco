import gridtiler

gridtiler(
    "/home/juju/gisco/building_demography/building_demography.csv",
    '/home/juju/Bureau/test_tiling',
    100,
    #tile_size_cell = 128,
    x_origin = 2500000,
    y_origin = 1000000,
    crs = "EPSG:3035"
)
