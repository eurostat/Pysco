from datetime import datetime

import pandas as pd

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.csvutils import hypercube_to_timeseries




def decompose_statistics_timeseries(params, services=None):
    """
    Decompose stat hypercive into single files with GEO and time series
    """

    sus = params["stat_units"]

    # output folder
    output_folder = params["out_folder"]
    os.makedirs(output_folder, exist_ok=True)

    if services is None: services = params["accessibility_grid_versions"].keys()

    for su in sus.keys():

        geo = su + "_" + sus[su]["version"]
        for service in services:

            for mode in params["modes_stats"][service].keys():
                mode_unit = params["modes_stats"][service][mode]["mode_unit"]
                print(datetime.now(), "decompose by time series", geo, service, mode, mode_unit)

                ofo = output_folder + "euro_access_" + service + "_" + geo + "_" + mode + "_" + mode_unit + "_" + params["stats_versions"][service]
                df = pd.read_parquet(ofo + ".parquet")

                if su == "LAU":
                    print(len(df))
                    df = df[df["ACCESS_INDIC"] == "N1"].drop(columns="ACCESS_INDIC")
                    print(len(df))
                    df = df[df["AGE"] == "T"].drop(columns="AGE")
                    print(len(df))
                    df = df[df["DEG_URB"] == "TOTAL"].drop(columns="DEG_URB")
                    print(len(df))
                    df = df[df["STATINFO"].isin(["AVG", "MED"])].drop(columns="STATINFO")
                    print(len(df))
                    df = df.drop(columns="UNIT")
                    print(len(df))
                    #GEO,ACCESS_INDIC,TRA_MODE,AGE,DEG_URB,STATINFO,UNIT,TIME,VALUE
                    #AT001C,N1,CAR,T,TOTAL,TOTAL,NR,2023,1984002.0


                if len(df) == 0: continue

                out_folder_d = output_folder + "stats_as_timeseries/" + geo + "_" + service + "/"
                os.makedirs(out_folder_d, exist_ok=True)

                hypercube_to_timeseries(df, out_folder_d)
                #hypercube_to_timeseries_large(df, out_folder_d)

