import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
#from utils.featureutils import iter_features
from utils.aggregate_geotiff import aggregate_geotiff_to_regions


# see /utils/aggregate_geotiff.py

nuts_version = "2024"

#nuts_lvl = "3"
#su = iter_features(f"/home/juju/geodata/gisco/CNTR_RG_100K_{nuts_version}_3035.gpkg", where="STAT_LEVL_CODE = " + str(nuts_lvl))
#su = list(su)
#print("Number of features: ", len(su))

aggregate_geotiff_to_regions(
    gpkg_path=f"/home/juju/geodata/gisco/CNTR_RG_100K_{nuts_version}_3035.gpkg",
    region_id_attr="NUTS_ID",
    geotiff_path=f"/home/juju/gisco/accessibility/euro_access_evrp_2025_1000m_v2026_06.tif",
    output_csv_path=f"/home/juju/gisco/accessibility/stats/evrp_2025_v2026_06.csv"
)

