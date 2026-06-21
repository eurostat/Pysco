from datetime import datetime
import pandas as pd

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.grid2stat import aggregate_geotiff_to_regions
from accessibility.utils import get_countries_covered
from accessibility.utils import bbox

# output folder
output_folder = "/home/juju/gisco/accessibility/stats/"
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
        "T": lambda v:True,
        "LT_5_MIN": lambda v: (v<=5*60) & (v>=0),
        "LT_20_MIN": lambda v: (v<=20*60) & (v>=0),
        "LT_45_MIN": lambda v: (v<=45*60) & (v>=0),
    },
    "education" : {
        "T": lambda v:True,
        "LT_2_MIN": lambda v: (v<=2*60) & (v>=0),
        "LT_10_MIN": lambda v: (v<=10*60) & (v>=0),
        "LT_20_MIN": lambda v: (v<=20*60) & (v>=0),
    },
    "evrp" : {
        "T":(0, 1e9),
        "LT_500_M": lambda v: (v<=500) & (v>=0),
        "LT_5000_M": lambda v: (v<=5000) & (v>=0),
    },
}

#degurba_raster = "/home/juju/geodata/gisco/degurba/DGURBA_LEVEL2_GRD_2021/DGUR_LEVEL2_GRD_1KM_2021_extended.tif"



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



su = "NUTS"
id_att = sus[su]["id"]
geo = su + "_" + sus[su]["version"]

service = "healthcare"
df = None
for year in acc_grids_versions[service].keys():
    print(datetime.now(), su, service, year)
    df_year = aggregate_geotiff_to_regions(
        gpkg_path=sus[su]["path"],
        region_id_attr=id_att,
        region_filter = zonal_filter(id_att, service, year),
        geotiff_path=pop_rasters[res],
        band=1,
        geotiff_mask_path = acc_grids_folder + "euro_access_" + service + "_" + year + "_" + res + "m_" + acc_grids_versions[service][year] + ".tif",
        geotiff_mask_fun= classes[service],
        block_size=4096,
        #geotiff_mask_path=degurba_raster,
        #geotiff_mask_fun= lambda v:v==130,
        #verbose=True,
    )
    df_year["TIME"] = year
    df = df_year if df is None else pd.concat([df, df_year], ignore_index=True)

df["UNIT"] = 'NR'
df = df.rename(columns={id_att: 'GEO', 'dim': 'INDIC', 'value': 'VALUE'})[["GEO","TIME","UNIT","INDIC","VALUE"]]

# compute percentages
if True:
    # Get the totals (INDIC='T') for each GEO/TIME combination
    totals = df[df['INDIC'] == 'T'][['GEO', 'TIME', 'VALUE']].rename(columns={'VALUE': 'TOTAL'})

    # Merge totals back onto the full dataframe
    df_merged = df.merge(totals, on=['GEO', 'TIME'])

    # Build the percentage rows
    pc_rows = df_merged.copy()
    pc_rows['VALUE'] = (pc_rows['VALUE'] / pc_rows['TOTAL'] * 100).round(2)
    pc_rows['UNIT'] = 'PC'

    # Drop the helper column and append
    pc_rows = pc_rows.drop(columns=['TOTAL']).query("INDIC != 'T'")
    df = pd.concat([df, pc_rows], ignore_index=True)


# TODO sort ?
print(datetime.now(), "save compiled file")
df.to_csv("tmp/" + "euro_access_" + service + "_" + geo + ".csv", index=False)





# generate mask files in TMP

# for accessibility grids, for the threshold - 1 per service, per year, per category (per indicator ?)
# for degurba 2 - one per category (3)
# for population by age: no need - one age group per band alreay

# for each SU type
# multiply acc X degurba




