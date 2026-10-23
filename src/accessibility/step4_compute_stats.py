import pandas as pd
from datetime import datetime
import shutil
from utils.utils import normalize

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.grid2stat import grid2stat_threshold, grid2stat_weighted_average
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
    #"education" : ["N1"],
    "education" : ["N1","AN3"],
    "evrp" : ["N1","AN5"],
}

access_classes = {
    "healthcare" : {
        "TOTAL": lambda v:True,
        "GT_5_MN": lambda v: (v>=5*60), # & (v>=0),
        "GT_10_MN": lambda v: (v>=10*60), # & (v>=0),
        "GT_20_MN": lambda v: (v>=20*60), # & (v>=0),
        "GT_45_MN": lambda v: (v>=45*60), # & (v>=0),
    },
    "education" : {
        "TOTAL": lambda v:True,
        "GT_2_MN": lambda v: (v>=2*60), # & (v>=0),
        "GT_10_MN": lambda v: (v>=10*60), # & (v>=0),
        "GT_15_MN": lambda v: (v>=15*60), # & (v>=0),
        "GT_20_MN": lambda v: (v>=20*60), # & (v>=0),
    },
    "evrp" : {
        "TOTAL": lambda v:True,
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
    "DEG130": lambda v: v==130,
    "DEG223": lambda v: v==223,
    "DEG222": lambda v: v==222,
    "DEG221": lambda v: v==221,
    "DEG313": lambda v: v==313,
    "DEG312": lambda v: v==312,
    "DEG311": lambda v: v==311,
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
        #if service == "education" and id in ["ES51", "ES511", "ES512", "ES513", "ES514", "ITC2", "ITH1", "ITC20", "ITH10", "ITH2", "ITH20"]:
        #    return False
        # if the id contains on of the country codes covered, then keep, else exclude
        for cnt in cnts:
            if cnt in id: return True
        return False
    return out



def compute_statistics(params, services=None, years=None, decompose_timeseries=True, compute_percentages=True):
    """
    Compute statistics for accessibility (thresholds number/percentages, averages and medians) and save to CSV and Parquet files.
    Structure: GEO,TRA_MODE,TIME,AGE,DEG_URB,ACCESS_INDIC,STATINFO,UNIT,VALUE
    """

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

            for mode in params["modes_stats"][service].keys():
                grid_mode = params["modes_stats"][service][mode]["grid_mode"]
                mode_unit = params["modes_stats"][service][mode]["mode_unit"]
                coeff = params["modes_stats"][service][mode]["coeff"]

                ofo = output_folder + "euro_access_" + geo + "_" + service + "_" + mode + "_" + mode_unit + "_" + params["stats_versions"][service]
                if os.path.exists(ofo + ".csv"): continue

                # make a single csv hypercube file per statunit and service
                df = None

                for ai in service_to_access_indicator[service]:

                    if years is None: years = params["accessibility_grid_versions"][service].keys()
                    for year in years:
                        for age_group in age_group_to_band.keys():
                            res = res_default if age_group == "T" else "1000"

                            print(datetime.now(), su, service, ai, mode, "(", grid_mode, mode_unit, coeff, ")", year, age_group, res)

                            # compute aggregated statistics, with masks
                            df_ = grid2stat_threshold(
                                population_path = pop_rasters[res],
                                population_band = age_group_to_band[age_group],

                                region_path = sus[su]["path"],
                                region_id_att = region_id_att,
                                region_filter = region_filter(region_id_att, service, year),

                                masks = [
                                    # accessibility threshold classes
                                    {
                                        "path" : params["out_folder"] + "euro_access_" + service + "_" + year + "_" + grid_mode + "_" + res + "m_" + params["accessibility_grid_versions"][service][year] + ".tif",
                                        "dim_name" : "STATINFO",
                                        "fun" : access_classes[service],
                                        "band" : access_indicator_to_band[ai],
                                        "coeff" : coeff
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
                            df_["TRA_MODE"] = mode
                            df_["AGE"] = age_group
                            df_["ACCESS_INDIC"] = ai
                            df_["VALUE"] = normalize(df_["VALUE"].round())
                            df_["UNIT"] = 'NR'
                            df_ = df_.rename(columns={region_id_att: 'GEO'})

                            # compute percentages
                            if compute_percentages:
                                # Get the totals (ACCESS_INDIC='T') for each GEO/TIME/AGE combination
                                totals = df_[df_['STATINFO'] == 'TOTAL'][['GEO', 'TIME', 'TRA_MODE', 'AGE', "DEG_URB", "ACCESS_INDIC", 'VALUE']].rename(columns={'VALUE': 'TOTAL'})

                                # Merge totals back onto the full dataframe
                                df_merged = df_.merge(totals, on=['GEO', 'TIME', 'TRA_MODE', 'AGE', "DEG_URB", "ACCESS_INDIC"])

                                # Build the percentage rows
                                pc_rows = df_merged.copy()
                                pc_rows['VALUE'] = (pc_rows['VALUE'] / pc_rows['TOTAL'] * 100).round(2)
                                pc_rows['UNIT'] = 'PC'

                                # Drop the helper column and append
                                pc_rows = pc_rows.drop(columns=['TOTAL']).query("STATINFO != 'TOTAL'")

                                df_ = pd.concat([df_, pc_rows], ignore_index=True)

                            # merge
                            df = df_ if df is None else pd.concat([df, df_], ignore_index=True)


                            # compute averages and median, with masks
                            df_ = grid2stat_weighted_average(
                                indic_path = params["out_folder"] + "euro_access_" + service + "_" + year + "_" + grid_mode + "_" + res + "m_" + params["accessibility_grid_versions"][service][year] + ".tif",
                                indic_band = access_indicator_to_band[ai],
                                weight_path =  pop_rasters[res],
                                weight_band = age_group_to_band[age_group],
                                region_path=sus[su]["path"],
                                region_id_att=region_id_att,
                                region_filter=region_filter(region_id_att, service, year),
                                masks= [
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
                            df_["TRA_MODE"] = mode
                            df_["UNIT"] = mode_unit
                            df_["AGE"] = age_group
                            df_["ACCESS_INDIC"] = ai
                            sec_to_mn = 60 if mode_unit == "MN" else 1 # to convert seconds to minutes if needed
                            df_["VALUE"] = (coeff * df_["VALUE"] / sec_to_mn).round(2)
                            df_ = df_.rename(columns={region_id_att: 'GEO'})

                            df = df_ if df is None else pd.concat([df, df_], ignore_index=True)



                # sort columns
                df = df[["GEO",'TRA_MODE',"AGE","DEG_URB","ACCESS_INDIC","STATINFO","UNIT","TIME","VALUE"]]

                # TODO remove no data rows ?

                # sort
                df = df.sort_values(["GEO","TRA_MODE","AGE","DEG_URB","ACCESS_INDIC","STATINFO","UNIT","TIME"])

                print(datetime.now(), "save compiled file")
                df.to_csv(ofo + ".csv", index=False)
                df.to_parquet(ofo + ".parquet")
                del df

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












# DEPRECATED
def compute_statistics_average(params, services=None, years=None, decompose_timeseries=True, compute_percentages=True):
    """
    Compute statistics for accessibility averages and save to CSV and Parquet files.
    GEO,TRA_MODE,TIME,AGE,DEG_URB,ACCESS_INDIC,STATINFO,UNIT,VALUE
    """

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

            ofo = output_folder + "euro_access_" + geo + "_" + service + "_AVG_MED_" + params["stats_versions"][service]
            if os.path.exists(ofo + ".csv"): continue

            # make a single csv hypercube file per statunit and service
            df = None

            for ai in service_to_access_indicator[service]:
                for mode in params["modes"][service]:

                    if years is None: years = params["accessibility_grid_versions"][service].keys()
                    for year in years:
                        for age_group in age_group_to_band.keys():
                            res = res_default if age_group == "T" else "1000"

                            print(datetime.now(), "average", su, service, ai, mode, year, age_group, res)

                            # compute aggregated statistics, with masks
                            df_ = grid2stat_weighted_average(
                                indic_path = params["out_folder"] + "euro_access_" + service + "_" + year + "_" + mode + "_" + res + "m_" + params["accessibility_grid_versions"][service][year] + ".tif",
                                indic_band = access_indicator_to_band[ai],
                                weight_path =  pop_rasters[res],
                                weight_band = age_group_to_band[age_group],
                                region_path=sus[su]["path"],
                                region_id_att=region_id_att,
                                region_filter=region_filter(region_id_att, service, year),
                                masks= [
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
                            df_["TRA_MODE"] = mode.split("_")[0]
                            df_["UNIT"] = mode.split("_")[1]
                            df_["AGE"] = age_group
                            df_["ACCESS_INDIC"] = ai

                            df_["VALUE"] = df_["VALUE"].round() #.astype(int)

                            df = df_ if df is None else pd.concat([df, df_], ignore_index=True)

            # rename and sort columns
            df = df.rename(columns={region_id_att: 'GEO'})[["GEO","TIME",'TRA_MODE',"AGE","DEG_URB","ACCESS_INDIC","STATINFO","UNIT","VALUE"]]

            # sort
            df.sort_values(["GEO",'TRA_MODE',"AGE","DEG_URB","ACCESS_INDIC","STATINFO","UNIT","TIME"])

            print(datetime.now(), "save compiled file")
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


