from datetime import datetime

import pandas as pd

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.csvutils import hypercube_to_timeseries_large




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
                if len(df) == 0: continue

                out_folder_d = output_folder + "stats_as_timeseries/" + geo + "_" + service + "/"
                os.makedirs(out_folder_d, exist_ok=True)

                #hypercube_to_timeseries(df, out_folder_d)
                hypercube_to_timeseries_large(df, out_folder_d)

