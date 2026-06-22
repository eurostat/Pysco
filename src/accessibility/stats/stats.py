from datetime import datetime
from math import isnan
import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.raster_class_pop import zonal_sum_by_class
from accessibility.utils import get_countries_covered
from utils.csvutils import hypercube_csv_to_timeseries_csv


# TODO
# advance mask
# stats by age group: educ for young, healthcare for old
# stats by degree of urbanisation
# run with 100 !!!
# filter correctly countries: remove those without population (AL, etc.)
# use also indicator to the X nearest ?
# faster ?
# make it possible that population raster is finer than class grid


# output folder
output_folder = "/home/juju/gisco/accessibility/stats/"
# accessiblity grids folder
acc_grids_folder = "/home/juju/gisco/accessibility/"

# resolution of the grids to use
res = "100"


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

# accessibility grids
acc_grids_versions = {
    "healthcare" : { "2020": "v2026_04", "2023": "v2026_04", },
    "education" : { "2020": "v2026_04", "2023": "v2026_04", },
    "evrp" : { "2023": "v2026_05", "2024": "v2026_05", "2025": "v2026_06", },
}

# classes
classes = {
    "healthcare" : {
        "pop_T":(0, 1e9),
        "pop_LT_5_MIN": (0, 5*60),
        "pop_LT_20_MIN": (0, 20*60),
        "pop_LT_45_MIN": (0, 45*60),
    },
    "education" : {
        "pop_T":(0, 1e9),
        "pop_LT_2_MIN": (0, 2*60),
        "pop_LT_10_MIN": (0, 10*60),
        "pop_LT_20_MIN": (0, 20*60),
    },
    "evrp" : {
        "pop_T":(0, 1e9),
        "pop_LT_500_M": (0, 500),
        "pop_LT_5000_M": (0, 5000),
    },
}

# function to determine the countries not covered by service and year
def zonal_filter(id_att:str, service:str, year:str):
    cnts = get_countries_covered(service, year)
    def out(r):
        if cnts == "all": return True
        # if the id contains on of the country codes covered, then keep, else exclude
        id = r[id_att]
        for cnt in cnts:
            if cnt in id: return True
        return False
    return out



for su in sus.keys():
    id_att = sus[su]["id"]
    geo = su + "_" + sus[su]["version"]
    for service in acc_grids_versions.keys():

        if True:
            out = []
            for year in acc_grids_versions[service].keys():
                print(datetime.now(), service, su, year, res)
                file_name = output_folder + service + "_" + su + "_" + year

                df = zonal_sum_by_class(
                    classes_path = acc_grids_folder + "euro_access_" + service + "_" + year + "_" + res + "m_" + acc_grids_versions[service][year] + ".tif",
                    values_path = pop_rasters[res],
                    zonal_path = sus[su]["path"],
                    zonal_filter = zonal_filter(id_att, service, year),
                    classes = classes[service],
                    id_att= id_att,
                    verbose = False,
                    clean_zonal_attributes = True
                ).drop(columns=['geometry'])

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
                        ob['INDIC'] = k.replace("pop_","").replace("pct_","")
                        ob['VALUE'] = row[k]
                        out.append(ob)

            # sort by NUTS level and alphabetic order
            #df = df.sort_values(id_att, key=lambda s: s.apply(lambda x: (len(x), x)))
            print(datetime.now(), "save compiled file")
            pd.DataFrame(out).to_csv(output_folder + "euro_access_" + service + "_" + geo + ".csv", index=False)


        if True:
            print(datetime.now(), "decompose by time series")

            out_folder_d = output_folder + "decomposed/"
            hypercube_csv_to_timeseries_csv(
                output_folder + "euro_access_" + service + "_" + geo + ".csv",
                out_folder_d,
                output_file_name_fun = lambda f: "euro_access_" + service + "_" + geo + "__" + f)

            # delete NR files (not usefull) and rename files (remove PC)
            for f in os.listdir(out_folder_d):
                if "__UNIT_NR" in f: os.remove(os.path.join(out_folder_d, f))
                if "__UNIT_PC" in f: os.rename(os.path.join(out_folder_d, f), os.path.join(out_folder_d, f.replace("__UNIT_PC", "")))





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