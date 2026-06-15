from datetime import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
#from utils.featureutils import iter_features
from utils.grid2stat import aggregate_geotiff_to_regions

# compute products
# compute ratios of the results
# compute nb services per LAU-NUTS - per category? check CHr file


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

