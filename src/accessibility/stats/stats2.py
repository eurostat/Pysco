from datetime import datetime

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.grid2stat import aggregate_geotiff_to_regions
#from utils.geotiff import crop_extend_bbox
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
        "LT_5_MIN": lambda v: v<=5*60,
        "LT_20_MIN": lambda v: v<=20*60,
        "LT_45_MIN": lambda v: v<=45*60,
    },
    "education" : {
        "T": lambda v:True,
        "LT_2_MIN": lambda v: v<=2*60,
        "LT_10_MIN": lambda v: v<=10*60,
        "LT_20_MIN": lambda v: v<=20*60,
    },
    "evrp" : {
        "T":(0, 1e9),
        "LT_500_M": lambda v: v<=500,
        "LT_5000_M": lambda v: v<=5000,
    },
}


degurba_raster = "/home/juju/geodata/gisco/degurba/DGURBA_LEVEL2_GRD_2021/DGUR_LEVEL2_GRD_1KM_2021_extended.tif"




su = "NUTS"
service = "healthcare"
year = "2023"
print(datetime.now(), su)
df = aggregate_geotiff_to_regions(
    gpkg_path=sus[su]["path"],
    region_id_attr=sus[su]["id"],
    geotiff_path=pop_rasters["1000"],
    band=1,
    geotiff_mask_path = acc_grids_folder + "euro_access_" + service + "_" + year + "_" + res + "m_" + acc_grids_versions[service][year] + ".tif",
    geotiff_mask_fun= classes[service],
    #geotiff_mask_path=degurba_raster,
    #geotiff_mask_fun= lambda v:v==130,
    #verbose=True,
)
#print(df)
df.to_csv("tmp/out.csv", index=False)





# generate mask files in TMP

# for accessibility grids, for the threshold - 1 per service, per year, per category (per indicator ?)
# for degurba 2 - one per category (3)
# for population by age: no need - one age group per band alreay

# for each SU type
# multiply acc X degurba




