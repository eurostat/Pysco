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


def aggregate():
    for year in ["2018","2021"]:
        for resolution in [1000, 2000, 5000, 10000, 20000, 50000, 100000]:
            for indicator in ["nearby_population", "accessible_population"]:
                print("aggregate", year, indicator, resolution)
                resample_geotiff_aligned(
                    f0 + "nearby_population_" + year + "_1000m.tif",
                    folder+indicator+"_" +year+"_"+str(resolution)+".tif",
                    resolution, Resampling.average)
            np = folder+"nearby_population"+"_" +year+"_"+str(resolution)+".tif"
            ap = folder+"accessible_population"+"_" +year+"_"+str(resolution)+".tif"
            rp = folder+"road_performance"+"_" +year+"_"+str(resolution)+".tif"
            combine_geotiffs([np, ap], rp, compress="deflate", dtype=np.int64)
            add_ratio_band(rp, 2, 1)
            os.remove(np)
            os.remove(ap)


def tiling():
    for indicator in ["nearby_population", "accessible_population"]:
        for resolution in [1000, 2000, 5000, 10000, 20000, 50000, 100000]:
            folder_ = folder + indicator + "_" + resolution + "/"
            if not os.path.exists(folder_): os.makedirs(folder_)

            year = "2021"
            tiff = folder + "road_performance_"+year+"_1000m.tif"

            pop_file = "/home/juju/geodata/census/"+year+"/aggregated_tiff/pop_"+year+"_"+resolution+".tif"


#aggregate()
tiling()

