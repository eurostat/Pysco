from rasterio.enums import Resampling
import numpy as np

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import resample_geotiff_aligned


path = "/home/juju/gisco/degurba/"

for new_resolution in [10000, 5000, 2000, 1000]:
    print("resampling", new_resolution)
    resample_geotiff_aligned(path + "GHS-DUG_GRID_L2.tif", path + "/out/"+str(new_resolution)+".tif", new_resolution, resampling=Resampling.mode, dtype=np.int8)

