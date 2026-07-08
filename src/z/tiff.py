import sys
import os
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import crop_extend_bbox, resample_geotiff_aligned, Resampling
from utils.convert import gpkg_grid_to_geotiff


# pop grid gpkg to geotiff
if False:
    gpkg_grid_to_geotiff(
        [ "/home/juju/geodata/gisco/grids/grid_1km_surf.gpkg" ],
        "/home/juju/geodata/census/pop_20XX_1000m.tif",
        grid_id_field="GRD_ID",
        attributes=["TOT_P_2006","TOT_P_2011","TOT_P_2018","TOT_P_2021"],
        bbox=[ 900000, 900000, 6600000, 5500000 ],
        compress="DEFLATE",
        dtype="int32",
        tiff_nodata_value=-9999
    )

# resample population geotiffs at different resolutions
if True:
    for resolution in [2000,5000,10000,20000,50000,100000]:
        print(f"Resampling to {resolution}m...")
        resample_geotiff_aligned("/home/juju/geodata/census/pop_20XX_1000m.tif",
                                "/home/juju/geodata/census/pop_20XX_"+str(resolution)+"m.tif",
                                resolution,
                                resampling=Resampling.sum,
                                dtype=np.int32,
                                )



# crop extend - adjust geotiff bbox
if False:
    crop_extend_bbox(
        "/home/juju/geodata/gisco/degurba/DGURBA_LEVEL2_GRD_2011/DGUR_LEVEL2_GRD_1KM_2011.tif",
        [ 900000, 900000, 6600000, 5500000 ],
        "/home/juju/geodata/gisco/degurba/DGURBA_LEVEL2_GRD_2011/DGUR_LEVEL2_GRD_1KM_2011_extended.tif",
        fill_value=310
    )

