import os
import pandas as pd
from pygridmap import gridtiler

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.gridutils import gpkg_point_to_csv

prepare_csv = False
aggregate = False
tiling = True

#
services_path = "/home/juju/geodata/gisco/basic_services/"
version_tag = "20260421"

if not os.path.exists("tmp/"): os.makedirs("tmp/")

for service in ["healthcare", "education"]:
    for year in ["2020", "2023"]:
        print(service, year)
        csv_file = "tmp/" + service + "_" + year + "_10_" + version_tag + ".csv"

        if prepare_csv:
            print("prepare csv")
            gpkg_point_to_csv(services_path + service + "_" + year + "_3035_" + version_tag + ".gpkg",
                            csv_file,
                            attributes_to_keep=["name" if service == "education" else "hospital_name"],
                            rounding_precision=-1)
            
            # remove rows without coordinates
            pd.read_csv(csv_file).dropna(subset=['x']).dropna(subset=['y']).to_csv(csv_file, index=False)

            #rename column for hospitals
            if service == "healthcare":
                pd.read_csv(csv_file).rename(columns={"hospital_name": "name"}).to_csv(csv_file, index=False)




        for a in [2, 5, 10, 20, 50, 100, 200, 500, 1000]:
            csva = "tmp/" + service + "_" + year + "_" + str(a*10) + "_" + version_tag + ".csv"

            if aggregate:
                print("aggregate",service, year, a)

                def aggregation_single_value(values, _): return values[0]

                gridtiler.grid_aggregation(
                    csv_file,
                    10,
                    csva,
                    a,
                    aggregation_fun = { "name": aggregation_single_value },
                )

                
            if tiling:
                print("tiling",service, year, a)
                resolution = a*10

                #create output folder
                folder = 'tmp/tiles_'+service+'_'+year+'/' + str(resolution)
                if not os.path.exists(folder): os.makedirs(folder)

                gridtiler.grid_tiling(
                    csva,
                    folder,
                    resolution,
                    tile_size_cell = 256,
                    x_origin = 0,
                    y_origin = 0,
                    crs = "EPSG:3035",
                    format = "parquet"
                )

