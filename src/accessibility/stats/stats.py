from datetime import datetime
import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.raster_class_pop import zonal_sum_by_class
from utils.csvutils import join_csv_files
from accessibility.utils import get_countries_covered


# TODO
# correct ? faster ?
# explode as hypercube
# stats by age group: educ for young, healthcare for old
# stats by degree of urbanisation
# make it possible that population raster is finer than class grid
# use also indicator to the X nearest ?

with_gpkg = False

# output folder
output_folder = "/home/juju/gisco/accessibility/stats/"
# working folder
working_folder = "./tmp/stats/"
# accessiblity grids folder
acc_grids_folder = "/home/juju/gisco/accessibility/"

# resolution of the grids to use
res = "1000"


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
        "pop_tot":(0, 1e9),
        "pop_under_5min": (0, 5*60),
        "pop_under_20min": (0, 20*60),
        "pop_under_45min": (0, 45*60),
    },
    "education" : {
        "pop_tot":(0, 1e9),
        "pop_under_2min": (0, 2*60),
        "pop_under_10min": (0, 10*60),
        "pop_under_20min": (0, 20*60),
    },
    "evrp" : {
        "pop_tot":(0, 1e9),
        "pop_under_500m": (0, 500),
        "pop_under_5000m": (0, 5000),
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



for service in acc_grids_versions.keys():
    for su in sus.keys():
        id_att = sus[su]["id"]
        out = []
        for year in acc_grids_versions[service].keys():
            print(datetime.now(), su, service, year, res)
            file_name = output_folder + service + "_" + su + "_" + year

            zonal_sum_by_class(
                classes_path = acc_grids_folder + "euro_access_" + service + "_" + year + "_" + res + "m_" + acc_grids_versions[service][year] + ".tif",
                values_path = pop_rasters[res],
                zonal_path = sus[su]["path"],
                zonal_filter = zonal_filter(id_att, service, year),
                classes = classes[service],
                gpkg_path = file_name + ".gpkg" if with_gpkg else None,
                csv_path = file_name + ".csv",
                id_att= id_att,
                verbose = False,
                class_name_change_fun = lambda cn: cn+"_"+year,
                #rounding_fun = lambda v : int(round(v))
                output_data_type = "Int64",
            )

            #
            df = pd.read_csv(file_name + ".csv")
            for index, row in df.iterrows():
                print(row.keys())
                #print(index, row['name'], row['age'])



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