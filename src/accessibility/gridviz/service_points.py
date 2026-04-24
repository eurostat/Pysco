import os
import pandas as pd
from pygridmap import gridtiler

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.gridutils import gpkg_point_to_csv

prepare_csv = True
aggregate = True
tiling = False

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
            
            #
            pd.read_csv(csv_file).dropna(subset=['x']).dropna(subset=['y']).to_csv(csv_file, index=False)

            #rename column for hospitals
            if service == "healthcare":
                pd.read_csv(csv_file).rename(columns={"hospital_name": "name"}).to_csv(csv_file, index=False)




        for a in [2, 5, 10, 20, 50, 100, 200, 500, 1000]:
            if aggregate:
                print("aggregate",service, year, a)

                def aggregation_single_value(values, _):
                    return values[0]

                csva = "tmp/" + service + "_" + year + "_" + str(a*10) + "_3035_" + version_tag + ".csv"
                gridtiler.grid_aggregation(
                    csv_file,
                    10,
                    csva,
                    a,
                    aggregation_fun = { "name": aggregation_single_value },
                )

                '''
            if tiling:
                print("tiling",service, year, a)

                #create output folder
                out_folder = 'pub/gridviz/leg2024/T1_bv/' + str(resolution)
                if not os.path.exists(folder): os.makedirs(folder)

                gridtiler.grid_tiling(
                    folder+str(resolution)+".csv",
                    out_folder,
                    resolution,
                    tile_size_cell = 256,
                    x_origin = 0,
                    y_origin = 0,
                    #crs = "EPSG:3035",
                    format = "parquet"
                )
'''

