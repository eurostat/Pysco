import pandas as pd
from datetime import datetime

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.grid2stat import grid2stat
from utils.csvutils import hypercube_csv_to_timeseries_csv


# TODO
# better filter country/regions
# degurba for 100m case
# make it possible that population raster is finer than class grid


# output folder
output_folder = "/home/juju/gisco/accessibility/stats/"
# accessiblity grids folder
acc_grids_folder = "/home/juju/gisco/accessibility/"

# resolution of the grids to use
res_default = "1000"


# the statistical units
sus = {
    "URAU": { "path": "/home/juju/geodata/gisco/URAU_RG_100K_2024_3035.gpkg" , "id": "URAU_CODE", "version":"2024" },
    "NUTS": { "path": "/home/juju/geodata/gisco/NUTS_RG_100K_2024_3035.gpkg", "id": "NUTS_ID", "version":"2024" },
    "LAU": { "path": "/home/juju/geodata/gisco/LAU_RG_100K_2024_3035.gpkg" , "id": "GISCO_ID", "version":"2024" },
}

# population rasters
pop_rasters = {
    "1000": "/home/juju/gisco/census_2021_v3_production/ESTAT_Census_2021_V3.tiff",
    "100": "/home/juju/geodata/jrc/JRC_CENSUS_2021_100m_grid/JRC-CENSUS_2021_100m_new_bbox.tif"
}


'''
Band 1: T
Band 2: M
Band 3: F
Band 4: Y_LT15
Band 5: Y_1564
Band 6: Y_GE65
'''
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

# accessibility grids
acc_grids_versions = {
    "healthcare" : { "2020": "v2026_04", "2023": "v2026_04", },
    "education" : { "2020": "v2026_04", "2023": "v2026_04", },
    "evrp" : { "2023": "v2026_05", "2024": "v2026_05", "2025": "v2026_06", },
}

# classes
access_classes = {
    "healthcare" : {
        "NONE": lambda v:True,
        "LT_5_MIN": lambda v: (v<=5*60) & (v>=0),
        "LT_20_MIN": lambda v: (v<=20*60) & (v>=0),
        "LT_45_MIN": lambda v: (v<=45*60) & (v>=0),
    },
    "education" : {
        "NONE": lambda v:True,
        "LT_2_MIN": lambda v: (v<=2*60) & (v>=0),
        "LT_10_MIN": lambda v: (v<=10*60) & (v>=0),
        "LT_20_MIN": lambda v: (v<=20*60) & (v>=0),
    },
    "evrp" : {
        "NONE": lambda v:True,
        "LT_500_M": lambda v: (v<=500) & (v>=0),
        "LT_5000_M": lambda v: (v<=5000) & (v>=0),
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
degurba_grid_path = "/home/juju/geodata/gisco/degurba/DGURBA_LEVEL2_GRD_2021/DGUR_LEVEL2_GRD_1KM_2021_extended.tif"
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
            "PL", "PT", "RO", "SK", "SI", "ES", "SE", "NO", "CH" ]
    def out(r):
        id = r[id_att]
        # skip special ones for education
        if service == "education" and id in ["CH", "ES51", "ES511", "ES512", "ES513", "ES514", "ITC2", "ITH1", "ITC20", "ITH10", "ITH2", "ITH20"]:
            return False
        # if the id contains on of the country codes covered, then keep, else exclude
        for cnt in cnts:
            if cnt in id: return True
        return False
    return out



for su in sus.keys():
    region_id_att = sus[su]["id"]
    geo = su + "_" + sus[su]["version"]
    for service in acc_grids_versions.keys():

        if True:
            # make a single csv hypercube file per statunit and service
            df = None

            for ai in service_to_access_indicator[service]:
                for year in acc_grids_versions[service].keys():
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
                                    "path" : acc_grids_folder + "euro_access_" + service + "_" + year + "_" + res + "m_" + acc_grids_versions[service][year] + ".tif",
                                    "dim_name" : "THRESHOLD",
                                    "fun" : access_classes[service],
                                    "band" : access_indicator_to_band[ai],
                                },
                                # degurba classes
                                {
                                    "path" : degurba_grid_path,
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
            if True:
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

            # TODO sort ?

            print(datetime.now(), "save compiled file")
            df.to_csv(output_folder + "euro_access_" + geo + "_" + service + ".csv", index=False)

        if True:
            print(datetime.now(), "decompose by time series", su, service)

            out_folder_d = output_folder + "as_timeseries/"
            hypercube_csv_to_timeseries_csv(
                output_folder + "euro_access_" + geo + "_" + service + ".csv",
                out_folder_d,
                output_file_name_fun = lambda f: "euro_access_" + geo + "_" + service + "__" + f)

            # delete NR files (not usefull) and rename files (remove PC)
            #for f in os.listdir(out_folder_d):
            #    if "__UNIT_NR" in f: os.remove(os.path.join(out_folder_d, f))
            #    if "__UNIT_PC" in f: os.rename(os.path.join(out_folder_d, f), os.path.join(out_folder_d, f.replace("__UNIT_PC", "")))







        '''
                print(datetime.now(), "compute percentages")
                for att in classes[service].keys():
                    if att == "pop_T": continue
                    def compute_percentage(r):
                        t = r['pop_T']
                        if not pd.notna(t) or t==0: return None
                        v = r[att]
                        if not pd.notna(v): return None
                        return round(100 * v/t, 2)
                    df[att.replace("pop","pct")] = df.apply(compute_percentage, axis=1)

                # take data for compiled file
                for index, row in df.iterrows():
                    for k in row.keys():
                        if k == id_att: continue
                        ob = { "GEO":row[id_att], "TIME":year }
                        if 'pop' in k: ob['UNIT'] = "NR"
                        else: ob['UNIT'] = "PC"
                        ob['THRESHOLD'] = k.replace("pop_","").replace("pct_","")
                        ob['VALUE'] = row[k]
                        out.append(ob)
        '''



'''
        print(datetime.now(), "join CSV all years")
        joined_file = output_folder + "euro_access_" + service + "_" + su + "_" + sus[su]["version"] + ".csv"
        join_csv_files(csvs, id_att, joined_file)
        for csv in csvs: os.remove(csv)

        print(datetime.now(), "compute percentages")
        df = pd.read_csv(joined_file)
        for year in acc_grids_versions[service].keys():
            for att in classes[service].keys():
                df[att.replace("pop","pct") + "_" +year] = df.apply(lambda row: round(100 * row[att + "_" +year] / row['pop_tot_' + year], 2) if row['pop_tot_' + year] != 0 else None, axis=1)
            df = df.drop(columns=['pct_tot_' + year])
        # sort by NUTS level and alphabetic order
        df = df.sort_values(id_att, key=lambda s: s.apply(lambda x: (len(x), x)))
        df.to_csv(joined_file, index=False)
'''



'''
# make combined file
#df = pd.DataFrame({ 'geo': [], 'serv': [], 'time': [], 'indic': [], 'unit': [], 'value': [] })
for service in acc_grids_versions.keys():
    rows = []
    for su in sus.keys():
        id_att = sus[su]["id"]
        file = output_folder + "euro_access_" + service + "_" + su + "_" + sus[su]["version"] + ".csv"
        # geo service year indic unit --- degurba age
        rows.append({'name': f'User{i}', 'age': 20 + i})

    pd.DataFrame(rows).to_csv(output_folder + "euro_access_" + service + "_" + sus.keys().join("_") + ".csv", index=False)
'''


'''

# produce population stats
# make mask geotiffs
# compute products
# join CSVs and compute ratios
# map stats on nuts + LAUs (joe)
# bonus: compute nb services per LAU-NUTS - per category? check CHr file


produce_population_stats = True




# make folders
os.makedirs(output_folder, exist_ok=True)
os.makedirs(working_folder, exist_ok=True)


# prepare total population per su
if produce_population_stats:
    for res in ["1000", "100"]:
        for su_name, su_info in su.items():

            print(datetime.now(), "produce T population from " +res+"m for "+su_name ) 
            aggregate_geotiff_to_regions(
                gpkg_path=su_info["path"],
                region_id_attr=su_info["id"],
                geotiff_path=pop_rasters[res],
                output_csv_path=working_folder + f"population_T_{su_name}_{res}m.csv",
                output_col_name="T",
            )
    #TODO do other categories from 1000m
'''




'''
print("Starting aggregation at: ", datetime.now())

aggregate_geotiff_to_regions(
    gpkg_path=f"/home/juju/geodata/gisco/NUTS_RG_100K_2024_3035.gpkg",
    region_id_attr="NUTS_ID",
    #gpkg_path=f"/home/juju/geodata/gisco/LAU_RG_100K_2024_3035.gpkg",
    #region_id_attr="GISCO_ID",
    geotiff_path=f"/home/juju/gisco/accessibility/euro_access_evrp_2025_100m_v2026_06.tif",
    output_csv_path=f"/home/juju/gisco/accessibility/stats/evrp_2025_v2026_06.csv",
    output_col_name="evrp_2025",
)

print("Finished aggregation at: ", datetime.now())

'''