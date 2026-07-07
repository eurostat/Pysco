import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import crop_extend_bbox


crop_extend_bbox(
    "/home/juju/geodata/gisco/degurba/DGURBA_LEVEL2_GRD_2011/DGUR_LEVEL2_GRD_1KM_2011.tif",
    [ 900000, 900000, 6600000, 5500000 ],
    "/home/juju/geodata/gisco/degurba/DGURBA_LEVEL2_GRD_2011/DGUR_LEVEL2_GRD_1KM_2011_extended.tif"
)

