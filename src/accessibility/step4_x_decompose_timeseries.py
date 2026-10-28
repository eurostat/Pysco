from datetime import datetime

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.csvutils import hypercube_to_timeseries




def decompose_statistics_timeseries(params, services=None, years=None):
    """
    Compute statistics for accessibility (thresholds number/percentages, averages and medians) and save to CSV and Parquet files.
    Structure: GEO,TIME,AGE,DEG_URB,STATINFO,UNIT,VALUE
    """

    sus = params["stat_units"]
    pop_rasters = params["pop_rasters"]

    # output folder
    output_folder = params["out_folder"]
    os.makedirs(output_folder, exist_ok=True)

    if services is None: services = params["accessibility_grid_versions"].keys()

    # resolution of the grids to use
    res_default = "1000"

    for su in sus.keys():
        geo = su + "_" + sus[su]["version"]
        for service in services:

            for mode in params["modes_stats"][service].keys():
                mode_unit = params["modes_stats"][service][mode]["mode_unit"]

                ofo = output_folder + "euro_access_" + service + "_" + geo + "_" + mode + "_" + mode_unit + "_" + params["stats_versions"][service]
                if os.path.exists(ofo + ".parquet"): continue
                print(datetime.now(), "decompose by time series", su, service)

                out_folder_d = output_folder + "stats_as_timeseries/" + geo + "/" + service + "_" + ai + "_" + mode + "_" + mode_unit + "/"
                os.makedirs(out_folder_d, exist_ok=True)

                hypercube_to_timeseries(df, out_folder_d)
