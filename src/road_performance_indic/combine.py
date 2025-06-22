# combine all tiff into a single one
# band on nearby pop, accessible pop, ratio

import sys
import os

import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import add_ratio_band, combine_geotiffs, rename_geotiff_bands, geotiff_mask_by_countries
from utils.convert import parquet_grid_to_geotiff


out_folder = '/home/juju/gisco/road_transport_performance/'
# whole europe
bbox = [ 900000, 900000, 6600000, 5500000 ]


for grid_resolution in ["1000"]:
    for year in ["2018"]:

        # ouput folder
        out_folder_year = out_folder + "out_" + year + "_" + str(grid_resolution) + "m/"
        if not os.path.exists(out_folder_year): os.makedirs(out_folder_year)

        geotiff_ap = out_folder + "accessible_population_" + year + "_" + grid_resolution + "m.tif"

        # check if tiff file was already produced
        # combine parquet files to a single tiff file
        if True: #not os.path.isfile(geotiff_ap):

            # get all parquet files in the output folder
            files = [os.path.join(out_folder_year, f) for f in os.listdir(out_folder_year) if f.endswith('.parquet')]
            if len(files)==0: continue

            print("transforming", len(files), "parquet files into tif for", year)
            parquet_grid_to_geotiff(
                files,
                geotiff_ap,
                bbox = bbox,
                dtype=np.int32,
                compress='deflate'
            )

            print("apply mask to force some countries to nodata")
            geotiff_mask_by_countries(
                geotiff_ap,
                geotiff_ap,
                gpkg = '/home/juju/geodata/gisco/CNTR_RG_100K_2024_3035.gpkg',
                gpkg_column = 'CNTR_ID',
                values = [
                    "AT", "BE", "BG", "HR", "CY", "CZ", "DE", "DK", "EE", "FI", "FR",
                    "EL", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
                    "PL", "PT", "RO", "SK", "SI", "ES", "SE", "NO", "CH"],
                #exclude: ["RS", "BA", "MK", "AL", "ME", "MD"],
                compress="deflate"
            )


        geotiff_np = out_folder + "nearby_population_" + year + "_" + grid_resolution + "m.tif"
        combined = out_folder + "road_performance_" + year + "_" + grid_resolution + "m.tif"

        print("combine geotiff", year, grid_resolution)
        combine_geotiffs([geotiff_np, geotiff_ap], combined, compress="deflate", dtype=np.int64)

        print("rename bands", year, grid_resolution)
        rename_geotiff_bands(combined, [ "np_" + year, "ap_" + year ])

        print("compute ratio", year, grid_resolution)
        add_ratio_band(combined, 2, 1, ratio_band_name='indic_'+year)

