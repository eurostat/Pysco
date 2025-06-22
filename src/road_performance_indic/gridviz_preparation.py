import numpy as np
from pygridmap import gridtiler_raster
import sys
import os
from rasterio.enums import Resampling

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import combine_geotiffs, resample_geotiff_aligned



f0 = "/home/juju/gisco/road_transport_performance/"
folder = f0 + "gridviz/"


def aggregate():
    for year in ["2018","2021"]:
        for indicator in ["nearby_population", "accessible_population"]:
            for resolution in [1000, 2000, 5000, 10000, 20000, 50000, 100000]:
                print("aggregate", year, indicator, resolution)
                infile = f0 + "nearby_population_" + year + "_1000m.tif"
                resample_geotiff_aligned(infile, folder+indicator+"_" +year+"_"+str(resolution)+".tif", resolution, Resampling.average)


def tiling():
    for indicator in ["np", "ap"]:
        for resolution in [1000, 2000, 5000, 10000, 20000, 50000, 100000]:
            folder_ = folder + indicator + "_" + resolution + "/"
            if not os.path.exists(folder): os.makedirs(folder)

            year = "2021"
            tiff = folder + "road_performance_"+year+"_1000m.tif"

            pop_file = "/home/juju/geodata/census/"+year+"/aggregated_tiff/pop_"+year+"_"+resolution+".tif"


aggregate()
