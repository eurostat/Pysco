import numpy as np
from pygridmap import gridtiler_raster
import sys
import os
from rasterio.enums import Resampling

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import combine_geotiffs, resample_geotiff_aligned


f0 = "/home/juju/gisco/road_transport_performance/"
folder = f0 + "gridviz/"

def tiling():
    for indicator in ["np", "ap", "rp"]:
        for resolution in [1000, 2000, 5000, 10000, 20000, 50000, 100000]:
            folder_ = folder + indicator + "_" + resolution + "/"
            if not os.path.exists(folder): os.makedirs(folder)

            year = "2021"
            tiff = folder + "road_performance_"+year+"_1000m.tif"

            pop_file = "/home/juju/geodata/census/"+year+"/aggregated_tiff/pop_"+year+"_"+resolution+".tif"


