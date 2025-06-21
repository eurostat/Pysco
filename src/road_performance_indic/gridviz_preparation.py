import numpy as np
from pygridmap import gridtiler_raster
import sys
import os
from rasterio.enums import Resampling

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import combine_geotiffs, resample_geotiff_aligned



f0 = "/home/juju/gisco/road_transport_performance/"
folder = f0 + "gridviz/"
if not os.path.exists(folder): os.makedirs(folder)


