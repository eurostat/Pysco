from datetime import datetime

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.grid2stat import aggregate_geotiff_to_regions
#from utils.geotiff import crop_extend_bbox
from accessibility.utils import bbox


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

degurba_raster = "/home/juju/geodata/gisco/degurba/DGURBA_LEVEL2_GRD_2021/DGUR_LEVEL2_GRD_1KM_2021_extended.tif"


su = "NUTS"
print(datetime.now(), su)
df = aggregate_geotiff_to_regions(
    gpkg_path=sus[su]["path"],
    region_id_attr=sus[su]["id"],
    geotiff_path=pop_rasters["1000"],
    band=1,
    output_csv_path="tmp/out.csv",
    output_col_name="T",
    #geotiff_mask_path=degurba_raster,
    #geotiff_mask_fun= lambda v:v==130,
    #verbose=True,
)
print(df)



# generate mask files in TMP

# for accessibility grids, for the threshold - 1 per service, per year, per category (per indicator ?)
# for degurba 2 - one per category (3)
# for population by age: no need - one age group per band alreay

# for each SU type
# multiply acc X degurba




