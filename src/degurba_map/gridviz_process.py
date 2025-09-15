from rasterio.enums import Resampling
import numpy as np

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import resample_geotiff_aligned


path = "/home/juju/gisco/degurba/"

new_resolution = 2000
resample_geotiff_aligned(path + "GHS-DUG_GRID_L2.tif", path + "/out/", new_resolution, resampling=Resampling.mode, dtype=np.int8)

