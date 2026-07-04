import os
import pandas as pd
from datetime import datetime
import shutil
from pygridmap import gridtiler

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.gridutils import gpkg_point_to_csv

def gridviz_tiling_points(params, services=None, years=None, prepare_csv=True, aggregate=True, tiling=True, zip_deploy=True):

    #
    out_folder = params["out_folder"] + "gridviz/pois/"

    # make missing folders
    if not os.path.exists(out_folder): os.makedirs(out_folder)
    if not os.path.exists("tmp/"): os.makedirs("tmp/")

    if services is None: services = params["pois_datasets"].keys()

    for service in services:

        years_ = params["pois_datasets"][service].keys() if years is None else years
        for year in years_:
            csv_file = "tmp/" + service + "_" + year + "_10" + ".csv"

            if prepare_csv:
                print(datetime.now(), "prepare csv", service, year)
                pois_path = params["pois_datasets"][service][year]
                gpkg_point_to_csv(pois_path,
                                csv_file,
                                attributes_to_keep= ["name"] if service == "education" else ["hospital_name"] if service == "healthcare" else [],
                                rounding_precision=-1)

                # remove rows without coordinates
                pd.read_csv(csv_file).dropna(subset=['x']).dropna(subset=['y']).to_csv(csv_file, index=False)

                #rename column for hospitals
                if service == "healthcare":
                    pd.read_csv(csv_file).rename(columns={"hospital_name": "name"}).to_csv(csv_file, index=False)


            for a in [2, 5, 10, 20, 50, 100, 200]:
                resolution = a*10
                csva = "tmp/" + service + "_" + year + "_" + str(resolution) + ".csv"

                if aggregate and a>1:
                    print(datetime.now(), "aggregate", service, year, resolution)

                    def aggregation_single_value(values, _): return values[0]

                    gridtiler.grid_aggregation(
                        csv_file,
                        10,
                        csva,
                        a,
                        aggregation_fun = {} if service == "evrp" else   { "name": aggregation_single_value },
                    )


                if tiling:
                    print(datetime.now(), "tiling", service, year, resolution)

                    # Create output folder
                    folder = out_folder + service + '/' + year + '/' + str(resolution)
                    if not os.path.exists(folder): os.makedirs(folder)

                    gridtiler.grid_tiling(
                        csva,
                        folder,
                        resolution,
                        tile_size_cell = 1024 if a>10 else 2048,
                        x_origin = -4100000,
                        y_origin = -3300000,
                        crs = "EPSG:3035",
                        format = "parquet"
                    )

    if zip_deploy:
        # zip and move tiles
        print(datetime.now(), "Zip tiles")
        shutil.make_archive(out_folder, "zip", out_folder + "/")
        print(datetime.now(), "Move zip file")
        shutil.move(out_folder + ".zip", params["deploy_target_folder"])
