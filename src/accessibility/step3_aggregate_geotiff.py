
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

        if years is None: years = params["accessibility_grid_versions"][service].keys()
        for year in years:
            for mode in params["modes"][service]:

                # it is better to resample all resolution from 100m one. Otherwise, we do medians of medians which may create some biais around places with many nodata pixels
                for resolution in resolutions:
                    print(datetime.now(), service, year, mode, resolution)

                    agg_tiff = folder_aggregated+"euro_access_"+service+"_" + year+"_"+mode+"_"+str(resolution) + "m_"+params["accessibility_grid_versions"][service][year]+".tif"
                    if os.path.exists(agg_tiff): continue

                    resample_geotiff_aligned(params["out_folder"] + "euro_access_"+service+"_"+year+"_"+mode+"_100m_"+params["accessibility_grid_versions"][service][year]+".tif",
                                            agg_tiff,
                                            resolution, Resampling.med)

                    # copy and deploy 1000m version
                    if resolution == 1000:
                        shutil.copy(folder_aggregated+"euro_access_"+service+"_"+year+"_"+mode+"_1000m_"+params["accessibility_grid_versions"][service][year]+".tif", params["out_folder"])
                        if "deploy_target_folder" in params:
                            shutil.copy(params["out_folder"]+"euro_access_"+service+"_"+year+"_"+mode+"_1000m_"+params["accessibility_grid_versions"][service][year]+".tif", params["deploy_target_folder"])

