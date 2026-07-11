import pandas as pd
from datetime import datetime
import shutil

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.grid2stat import grid2stat
from utils.csvutils import hypercube_csv_to_timeseries_csv

age_group_to_band = {
    "T":1,
    "Y_LT15":4,
    "Y_1564":5,
    "Y_GE65":6,
}

access_indicator_to_band = {
    "N1":1,
    "AN3":2,
    "AN5":2,
}
service_to_access_indicator = {
    "healthcare" : ["N1","AN3"],
    "education" : ["N1","AN3"],
    "evrp" : ["N1","AN5"],
}

access_classes = {
    "healthcare" : {
        "NONE": lambda v:True,
        "GT_5_MIN": lambda v: (v>=5*60), # & (v>=0),
        "GT_20_MIN": lambda v: (v>=20*60), # & (v>=0),
        "GT_45_MIN": lambda v: (v>=45*60), # & (v>=0),
    },
    "education" : {
        "NONE": lambda v:True,
        "GT_2_MIN": lambda v: (v>=2*60), # & (v>=0),
        "GT_10_MIN": lambda v: (v>=10*60), # & (v>=0),
        "GT_20_MIN": lambda v: (v>=20*60), # & (v>=0),
    },
    "evrp" : {
        "NONE": lambda v:True,
        "GT_500_M": lambda v: (v>=500), # & (v>=0),
        "GT_2000_M": lambda v: (v>=2000), # & (v>=0),
        "GT_5000_M": lambda v: (v>=5000), # & (v>=0),
    },
}


# use code DEG_URB
'''
TOTAL		Total		Y
DEG1_DEG2		Urban areas		Y
DEG1		Cities		Y
DEG2		Towns and suburbs		Y
DEG3		Rural areas		Y
NRP		No response		Y
UNK		Unknown		Y

130 = Urban Centre (was 30)
223= Dense Urban Custer (was 23)
222 = Semi dense Urban cluster (remains the same)
221 = Suburban/peri-urban grid cell (was 21)
313 = Rural cluster (was 13)
312 = Low density rural grid cell (was 12)
311 = Very low density rural grid cell (was 11)
310 = Water
'''
degurba_classes = {
    "TOTAL": lambda v:True,
    "DEG1": lambda v: v<200, # Cities
    "DEG2": lambda v: (v>200) & (v<300), # Towns and suburbs
    "DEG3": lambda v: (v>310), # Rural areas
}




# function to determine the countries not covered by service and year
def region_filter(id_att:str, service:str, year:str):
    cnts = ["AT", "BE", "BG", "HR", "CY", "CZ", "DE", "DK", "EE", "FI", "FR",
            "EL", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
            "PL", "PT", "RO", "SK", "SI", "ES", "SE", "NO" ]
    if service != "education": cnts.append("CH")
    def out(r):
        id = r[id_att]
        # skip special ones for education
        if service == "education" and id in ["ES51", "ES511", "ES512", "ES513", "ES514", "ITC2", "ITH1", "ITC20", "ITH10", "ITH2", "ITH20"]:
            return False
        # if the id contains on of the country codes covered, then keep, else exclude
        for cnt in cnts:
            if cnt in id: return True
        return False
    return out


def compute_statistics(params, services=None, decompose_timeseries=True, compute_percentages=True):

    sus = params["stat_units"]
    pop_rasters = params["pop_rasters"]

    # output folder
    output_folder = params["out_folder"] + "stats/"
    os.makedirs(output_folder, exist_ok=True)

    if services is None: services = params["accessibility_grid_versions"].keys()

    # resolution of the grids to use
    res_default = "1000"

    for su in sus.keys():
        region_id_att = sus[su]["id"]
        geo = su + "_" + sus[su]["version"]
        for service in services:

            # make a single csv hypercube file per statunit and service
            df = None

            for ai in service_to_access_indicator[service]:
                for year in params["accessibility_grid_versions"][service].keys():
                    for age_group in age_group_to_band.keys():
                        res = res_default if age_group == "T" else "1000"

                        print(datetime.now(), su, service, ai, year, age_group, res)

                        # compute aggregated statistics, with masks
                        df_ = grid2stat(
                            population_path = pop_rasters[res],
                            population_band = age_group_to_band[age_group],

                            region_path = sus[su]["path"],
                            region_id_att = region_id_att,
                            region_filter = region_filter(region_id_att, service, year),

                            masks = [
                                # accessibility threshold classes
                                {
                                    "path" : params["out_folder"] + "euro_access_" + service + "_" + year + "_" + res + "m_" + params["accessibility_grid_versions"][service][year] + ".tif",
                                    "dim_name" : "THRESHOLD",
                                    "fun" : access_classes[service],
                                    "band" : access_indicator_to_band[ai],
                                },
                                # degurba classes
                                {
                                    "path" : params["degurba_grid_path"],
                                    "dim_name" : "DEG_URB",
                                    "fun" : degurba_classes,
                                    "band" : 1,
                                },
                            ]
                        )
                        df_["TIME"] = year
                        df_["AGE"] = age_group
                        df_["ACCESS_INDIC"] = ai
                        df = df_ if df is None else pd.concat([df, df_], ignore_index=True)

            df["UNIT"] = 'NR'
            # rename and sort columns
            df = df.rename(columns={region_id_att: 'GEO', 'value': 'VALUE'})[["GEO","TIME","AGE","DEG_URB","ACCESS_INDIC","THRESHOLD","UNIT","VALUE"]]

            # compute percentages
            if compute_percentages:
                # Get the totals (ACCESS_INDIC='T') for each GEO/TIME/AGE combination
                totals = df[df['THRESHOLD'] == 'NONE'][['GEO', 'TIME', 'AGE', "DEG_URB", "ACCESS_INDIC", 'VALUE']].rename(columns={'VALUE': 'TOTAL'})

                # Merge totals back onto the full dataframe
                df_merged = df.merge(totals, on=['GEO', 'TIME', 'AGE', "DEG_URB", "ACCESS_INDIC"])

                # Build the percentage rows
                pc_rows = df_merged.copy()
                pc_rows['VALUE'] = (pc_rows['VALUE'] / pc_rows['TOTAL'] * 100).round(2)
                pc_rows['UNIT'] = 'PC'

                # Drop the helper column and append
                pc_rows = pc_rows.drop(columns=['TOTAL']).query("THRESHOLD != 'NONE'")
                df = pd.concat([df, pc_rows], ignore_index=True)

            # TODO remove no data rows ?

            # sort
            df.sort_values(["GEO","AGE","DEG_URB","ACCESS_INDIC","THRESHOLD","UNIT","TIME"])

            print(datetime.now(), "save compiled file")
            ofo = output_folder + "euro_access_" + geo + "_" + service + "_" + params["stats_versions"][service]
            df.to_csv(ofo + ".csv", index=False)
            df.to_parquet(ofo + ".parquet")

            if "deploy_target_folder" in params:
                print(datetime.now(), "deploy file")
                shutil.copy(ofo + ".csv", params["deploy_target_folder"])
                shutil.copy(ofo + ".parquet", params["deploy_target_folder"])

            if decompose_timeseries:
                print(datetime.now(), "decompose by time series", su, service)

                out_folder_d = output_folder + "as_timeseries/"
                os.makedirs(out_folder_d, exist_ok=True)

                hypercube_csv_to_timeseries_csv(
                    ofo + ".csv",
                    out_folder_d,
                    output_file_name_fun = lambda f: "euro_access_" + geo + "_" + service + "__" + f)


                # delete NR files (not usefull) and rename files (remove PC)
                #for f in os.listdir(out_folder_d):
                #    if "__UNIT_NR" in f: os.remove(os.path.join(out_folder_d, f))
                #    if "__UNIT_PC" in f: os.rename(os.path.join(out_folder_d, f), os.path.join(out_folder_d, f.replace("__UNIT_PC", "")))

