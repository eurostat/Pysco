from datetime import datetime
import numpy as np
import shutil

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.convert import parquet_grid_to_geotiff
from utils.geotiff import geotiff_mask_by_countries, rename_geotiff_bands



# define country codes for the countries covered, depending on the country and the year
def get_countries_covered(service:str, year:str):
    if service == "evrp": return "all"
    cnts = ["AT", "BE", "BG", "HR", "CY", "CZ", "DE", "DK", "EE", "FI", "FR",
            "EL", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
            "PL", "PT", "RO", "SK", "SI", "ES", "SE", "NO" ]
    #exclude: ["CH", "RS", "BA", "MK", "AL", "ME", "MD"],
    if service == "healthcare": cnts.append("CH")
    if year == "2023": cnts.append("AL")
    return cnts


def combine_to_geotiff(params, services=None, years=None, do_combination = True, resolutions=[100]):

    if services is None: services = params["accessibility_grid_versions"].keys()

    for resolution in resolutions:

        for service in services:

            k = 5 if service == "evrp" else 3
            if years is None: years = params["pois_datasets"][service].keys()

            for year in years:
                print(datetime.now(), resolution, service, year)

                # ouput folder
                out_folder_service_year = params["out_folder"] + "out_" + service + "_" + year + "_" + str(resolution) + "m/"
                if not os.path.exists(out_folder_service_year): continue

                # combine parquet files to a single tiff file
                geotiff = params["out_folder"] + "euro_access_" + service + "_" + year + "_" + str(resolution) + "m_"+ params["accessibility_grid_versions"][service][year] +".tif"

                # check if tiff file was already produced
                if os.path.isfile(geotiff) and do_combination:
                    print(datetime.now(), "Combined file already produced")
                    continue

                if do_combination:
                    # get all parquet files in the output folder
                    files = [os.path.join(out_folder_service_year, f) for f in os.listdir(out_folder_service_year) if f.endswith('.parquet')]
                    if len(files)==0:
                        print("No file to combine")
                        continue

                    print(datetime.now(), resolution, service, year, "transforming", len(files), "parquet files into tif for", service, year)
                    parquet_grid_to_geotiff(
                        files,
                        geotiff,
                        bbox = params["bbox"],
                        attributes=["cost_1", "cost_average_" + str(k)],
                        parquet_nodata_values=[-1],
                        dtype = np.int32 if service=="evrp" else np.int16,
                        value_fun= (lambda v:v) if service=="evrp" else (lambda v: (v if v<32767 else 32767)), # np.int16(v),
                        compress='deflate'
                    )
                    files.clear()
                    files = None

                print(datetime.now(), resolution, service, year, "apply mask to force some countries to nodata")
                if service != "evrp":
                    geotiff_mask_by_countries(
                        geotiff,
                        geotiff,
                        gpkg = params["country_gpkg"],
                        gpkg_column = 'CNTR_ID',
                        values = get_countries_covered(service, year),
                        compress="deflate",
                    )

                if service == "education":
                    print(datetime.now(), resolution, service, year, "apply mask to force some nuts regions to nodata")
                    geotiff_mask_by_countries(
                        geotiff,
                        geotiff,
                        gpkg = params["nuts_gpkg"],
                        gpkg_column = 'NUTS_ID',
                        values = ["ES51", "ITC2", "ITH1", "ITH2"],
                        compress="deflate",
                        invert=True,
                    )

                print(datetime.now(), resolution, service, year, "rename tiff bands")
                rename_geotiff_bands(geotiff, ["n1", "n" + str(k)])

                if "deploy_target_folder" in params:
                        print(datetime.now(), "Move zip file", service)
                        shutil.move(geotiff, params["deploy_target_folder"])
