import numpy as np
from pygridmap import gridtiler_raster
import sys
import os
from rasterio.enums import Resampling

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import combine_geotiffs, resample_geotiff_aligned, add_ratio_band



f0 = "/home/juju/gisco/road_transport_performance/"
folder = f0 + "gridviz/"
if not os.path.exists(folder): os.makedirs(folder)
pop_folder = "/home/juju/geodata/census/"

def aggregate():
    for year in ["2018","2021"]:
        for resolution in [1000, 2000, 5000, 10000, 20000, 50000, 100000]:
            for indicator in ["nearby_population", "accessible_population"]:
                print("aggregate", year, indicator, resolution)
                resample_geotiff_aligned(
                    f0 + indicator + "_" + year + "_1000m.tif",
                    folder+indicator+"_" +year+"_"+str(resolution)+".tif",
                    resolution, Resampling.average)
            np_ = folder+"nearby_population"+"_" +year+"_"+str(resolution)+".tif"
            ap = folder+"accessible_population"+"_" +year+"_"+str(resolution)+".tif"
            rp = folder+"road_performance"+"_" +year+"_"+str(resolution)+".tif"
            combine_geotiffs([np_, ap], rp, compress="deflate", dtype=np.int64)
            add_ratio_band(rp, 2, 1)
            os.remove(np_)
            os.remove(ap)



def tiling():
    for indicator in ["np", "ap", "rp"]:
       for resolution in [1000, 2000, 5000, 10000, 20000, 50000, 100000]:
            folder_ = folder + "tiles/" + indicator + "_" + str(resolution) + "/"
            if not os.path.exists(folder_): os.makedirs(folder_)

            band = 1 if indicator=="np" else 2 if indicator=="ap" else 3

            # prepare dict for geotiff bands
            #TODO population not correct ?! check bbox ?
            dict = {
                "v_2018" : { "file":folder+"road_performance"+"_2018_"+str(resolution)+".tif", "band":band },
                "v_2021" : { "file":folder+"road_performance"+"_2021_"+str(resolution)+".tif", "band":band },
                "pop_2018" : { "file":pop_folder+"2018/aggregated_tiff/pop_2018_"+str(resolution)+".tif", "band":1 },
                "pop_2021" : { "file":pop_folder+"2021/aggregated_tiff/pop_2021_"+str(resolution)+".tif", "band":1 },
            }

            # launch tiling
            gridtiler_raster.tiling_raster(
                dict,
                folder_,
                crs="EPSG:3035",
                tile_size_cell = 256,
                format="parquet",
                num_processors_to_use = 10,
                )


aggregate()
tiling()

