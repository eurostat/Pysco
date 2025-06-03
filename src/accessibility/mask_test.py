import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import geotiff_mask_by_countries


geotiff_mask_by_countries(
        '/home/juju/gisco/accessibility/euro_access_healthcare_2023_100m.tif',
        '/home/juju/gisco/accessibility/euro_access_healthcare_2023_100m_mask.tif',
        values_to_exclude = ["DE", "CH", "RS", "BA", "MK", "AL", "ME", "MD"],
        gpkg = '/home/juju/geodata/gisco/CNTR_RG_100K_2024_3035.gpkg',
        gpkg_column = 'CNTR_ID',
        compress="deflate",
)
