# combine all tiff into a single one
# band on nearby pop, accessible pop, ratio

import sys
import os

import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.geotiff import add_ratio_band, combine_geotiffs, rename_geotiff_bands


out_folder = '/home/juju/gisco/road_transport_performance/'

for grid_resolution in ["1000"]:
    for year in ["2021"]:

        geotiff_ap = out_folder + "accessible_population_" + year + "_" + grid_resolution + "m.tif"
        geotiff_np = out_folder + "nearby_population_" + year + "_" + grid_resolution + "m.tiff"
        combined = out_folder + "combined_" + year + "_" + grid_resolution + "m.tif"

        print("combine geotiff")
        combine_geotiffs([geotiff_np, geotiff_ap], combined, compress="deflate", dtype=np.int64)

        print("rename bands")
        rename_geotiff_bands(combined, [ "np_" + year, "ap_" + year ])

        print("compute ratio")
        add_ratio_band(combined, 2, 1, ratio_band_name='indic_'+year)

