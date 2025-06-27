# prepare accessibility grid for gridviz mapping

from pygridmap import gridtiler_raster
import sys
import os
from rasterio.enums import Resampling
from datetime import datetime
from math import round
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.geotiff import resample_geotiff_aligned


f0 = "/home/juju/gisco/accessibility/"
folder = f0 + "gridviz/"
if not os.path.exists(folder): os.makedirs(folder)

folder_pop_tiff = "/home/juju/geodata/census/2021/aggregated_tiff/"

# aggregate at various resolutions - average
def aggregate():

    for year in ["2023", "2020"]:
        for service in ["education", "healthcare"]:

            # it is better to resample all resolution from 100m one. Otherwise, we do averages of averages which may create some biais around places with many nodata pixels
            for resolution in [100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000]:
                print(datetime.now(), service, year, resolution)
                resample_geotiff_aligned(f0 + "euro_access_"+service+"_"+year+"_100m.tif", folder+"euro_access_"+service+"_" + year+"_"+str(resolution) + "m.tif", resolution, Resampling.average)

            '''
            print(service, year, 1000)
            resample_geotiff_aligned(folder+"euro_access_"+service+"_"+year+"_500m.tif", folder+"euro_access_"+service+"_" + year+"_1000m.tif", 1000, Resampling.average)

            for resolution in [2000, 5000, 10000]:
                print(service, year, resolution)
                resample_geotiff_aligned(folder+"euro_access_"+service+"_" + year+"_1000m.tif", folder+"euro_access_"+service+"_" + year+"_"+str(resolution)+"m.tif", resolution, Resampling.average)

            for resolution in [20000, 50000, 100000]:
                print(service, year, resolution)
                resample_geotiff_aligned(folder+"euro_access_"+service+"_" + year+"_10000m.tif", folder+"euro_access_"+service+"_" + year+"_"+str(resolution)+"m.tif", resolution, Resampling.average)
            '''

def tiling():

    for f in [ 1000, 500, 200, 100, 50, 20, 10, 5, 2, 1 ]: #, 1
        resolution = 100 * f

        for service in ["education", "healthcare"]:

            print(datetime.now(), "Tiling", service, resolution)

            # make folder for resolution
            folder_ = folder+"tiles/"+service+"_"+str(resolution)+"/"
            if not os.path.exists(folder_): os.makedirs(folder_)

            # prepare dict for geotiff bands
            dict = {}
            for year in ["2020", "2023"]:
                dict["dt_1_" + year] = {"file":folder+"euro_access_"+service+"_"+year+"_"+str(resolution)+"m.tif", "band":1}
                dict["dt_a3_" + year] = {"file":folder+"euro_access_"+service+"_"+year+"_"+str(resolution)+"m.tif", "band":2}
                dict["POP_2021"] = { "file":folder_pop_tiff+"pop_2021_"+str(resolution)+".tif", "band":1 }

            # launch tiling
            gridtiler_raster.tiling_raster(
                dict,
                folder_,
                crs="EPSG:3035",
                tile_size_cell = 256,
                format="parquet",
                num_processors_to_use = 10,
                modif_fun = round
                )


#print(datetime.now(), "aggregate")
#aggregate()

print(datetime.now(), "tiling")
tiling()

