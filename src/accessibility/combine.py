import numpy as np

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.convert import parquet_grid_to_geotiff
from utils.geotiff import geotiff_mask_by_countries, rename_geotiff_bands

# where to store the outputs
out_folder = '/home/juju/gisco/accessibility/'
country_gpkg = '/home/juju/geodata/gisco/CNTR_RG_100K_2024_3035.gpkg'
nuts_gpkg = '/home/juju/geodata/gisco/NUTS_RG_100K_2024_3035.gpkg'

services = ["education"] #education healthcare
years = ["2020"] #"2023" 2020
version_tag = "2025_11"
skip_combination = True

# whole europe
bbox = [ 900000, 900000, 6600000, 5500000 ]

for resolution in [100]:

    for service in services:

        for year in years:
            print(resolution, service, year)

            # ouput folder
            out_folder_service_year = out_folder + "out_" + service + "_" + year + "_" + str(resolution) + "m/"
            if not os.path.exists(out_folder_service_year): continue

            # combine parquet files to a single tiff file
            geotiff = out_folder + "euro_access_" + service + "_" + year + "_" + str(resolution) + "m_"+version_tag+".tif"

            # check if tiff file was already produced
            if os.path.isfile(geotiff) and not skip_combination:
                print("Combined file already produced")
                continue

            if not skip_combination:
                # get all parquet files in the output folder
                files = [os.path.join(out_folder_service_year, f) for f in os.listdir(out_folder_service_year) if f.endswith('.parquet')]
                if len(files)==0:
                    print("No file to combine")
                    continue

                print(resolution, service, year, "transforming", len(files), "parquet files into tif for", service, year)
                parquet_grid_to_geotiff(
                    files,
                    geotiff,
                    bbox = bbox,
                    attributes=["duration_s_1", "duration_average_s_3"],
                    parquet_nodata_values=[-1],
                    dtype=np.int16,
                    value_fun= lambda v:v if v<32767 else 32767, # np.int16(v),
                    compress='deflate'
                )
                files.clear()
                files = None

            print(resolution, service, year, "apply mask to force some countries to nodata")
            cnts = ["AT", "BE", "BG", "HR", "CY", "CZ", "DE", "DK", "EE", "FI", "FR",
                    "EL", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
                    "PL", "PT", "RO", "SK", "SI", "ES", "SE", "NO" ]
            #exclude: ["CH", "RS", "BA", "MK", "AL", "ME", "MD"],
            if service == "healthcare": cnts.append("CH")
            if year == "2023": cnts.append("AL")
            geotiff_mask_by_countries(
                geotiff,
                geotiff,
                gpkg = country_gpkg,
                gpkg_column = 'CNTR_ID',
                values = cnts,
                compress="deflate"
            )

            print(resolution, service, year, "apply mask to force some nuts regions to nodata")
            nuts = [] #TODO
            geotiff_mask_by_countries(
                geotiff,
                geotiff,
                gpkg = nuts_gpkg,
                gpkg_column = 'NUTS_ID',
                values = nuts,
                compress="deflate",
                invert=True
            )


            print(resolution, service, year, "rename tiff bands")
            rename_geotiff_bands(geotiff, [service + "_" + year + "_1", service + "_" + year + "_a3"])

