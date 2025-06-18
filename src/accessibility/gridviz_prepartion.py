

from pygridmap import gridtiler_raster

import os




folder = "/home/juju/gisco/accessibility/"


resolution = "1000"
for service in ["education"]:
    for year in ["2023"]:

        folder_ = folder+"tiles/"+service+"_"+year+"_"+resolution+"/"
        os.makedirs(folder_)

        file = "/home/juju/gisco/accessibility/euro_access_"+service+"_"+year+"_"+resolution+"m.tif"
        gridtiler_raster.tiling_raster(
            { "height": {"file":file, "band":1, 'no_data_values':[255,0]} }, #TODO
            folder_,
            crs="EPSG:3035",
            tile_size_cell=256,
            format="parquet",
            num_processors_to_use = 10,
            )

