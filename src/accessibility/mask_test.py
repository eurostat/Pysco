import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import geotiff_mask_by_countries, mask_raster_with_gpkg

for service in ["education", "healthcare"]:
        print(service)

        mask_raster_with_gpkg(
                '/home/juju/gisco/accessibility/euro_access_'+service+'_2023_100m.tif',
                '/home/juju/geodata/gisco/CNTR_RG_100K_2024_3035.gpkg',
                'CNTR_ID',
                ["DE", "CH", "RS", "BA", "MK", "AL", "ME", "MD"],
                '/home/juju/gisco/accessibility/euro_access_'+service+'_2023_100m_mask.tif',
                )

'''
        geotiff_mask_by_countries(
                '/home/juju/gisco/accessibility/euro_access_'+service+'_2023_100m.tif',
                '/home/juju/gisco/accessibility/euro_access_'+service+'_2023_100m_mask.tif',
                values_to_exclude = ["DE", "CH", "RS", "BA", "MK", "AL", "ME", "MD"],
                compress="deflate",
        )
'''
