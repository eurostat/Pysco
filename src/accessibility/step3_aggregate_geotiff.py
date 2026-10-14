
import sys
import os
import shutil
from rasterio.enums import Resampling
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import resample_geotiff_aligned


def aggregate_geotiff(params, services, years):

    if services is None: services = params["pois_datasets"].keys()

    resolutions = [ 100000, 50000, 20000, 10000, 5000, 2000, 1000, 500, 200, 100 ]

    folder_aggregated = params["out_folder"] + "aggregated/"
    if not os.path.exists(folder_aggregated): os.makedirs(folder_aggregated)

    # aggregate at various resolutions - median
    print(datetime.now(), "aggregate")
    for service in services:
        for year in params["accessibility_grid_versions"][service].keys():

            # it is better to resample all resolution from 100m one. Otherwise, we do medians of medians which may create some biais around places with many nodata pixels
            for resolution in resolutions:
                print(datetime.now(), service, year, resolution)
                resample_geotiff_aligned(params["out_folder"] + "euro_access_"+service+"_"+year+"_100m_"+params["accessibility_grid_versions"][service][year]+".tif",
                                        folder_aggregated+"euro_access_"+service+"_" + year+"_"+str(resolution) + "m_"+params["accessibility_grid_versions"][service][year]+".tif",
                                        resolution, Resampling.med)

            # copy and deploy 1000m version
            shutil.copy(folder_aggregated+"euro_access_"+service+"_"+year+"_1000m_"+params["accessibility_grid_versions"][service][year]+".tif", params["out_folder"])
            if "deploy_target_folder" in params:
                shutil.copy(params["out_folder"]+"euro_access_"+service+"_"+year+"_1000m_"+params["accessibility_grid_versions"][service][year]+".tif", params["deploy_target_folder"])
















    # TODO
    for service in services:
        for year in years:
            print(datetime.now(), service, year)
            combine_to_geotiff(
                params=params,
                services=[service],
                years=[year],
                do_combination=False,
                do_aggregation=True
            )
