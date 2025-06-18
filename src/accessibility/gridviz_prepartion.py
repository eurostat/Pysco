from pygridmap import gridtiler_raster
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import combine_geotiffs


f0 = "/home/juju/gisco/accessibility/"
folder = f0 + "gridviz/"
if not os.path.exists(folder): os.makedirs(folder)


# combine all necessary data into a single geotiff
def combine(resolution):
    # make list of files to combine
    tiffs = []
    for service in ["education", "healthcare"]:
        for year in ["2020", "2023"]:
            tiffs.append( f0 + "euro_access_"+service+"_"+year+"_"+resolution+"m.tif" )
    # combine files
    combine_geotiffs(tiffs, folder+resolution+"tiff", compress="deflate")



def aggregate():
    resample_geotiff_aligned()

    #file = "/home/juju/gisco/accessibility/euro_access_"+service+"_"+year+"_"+resolution+"m.tif"




def tiling():

    resolution = "1000"
    for service in ["education"]:
        for year in ["2023"]:

            folder_ = folder+"tiles/"+service+"_"+year+"_"+resolution+"/"
            if not os.path.exists(folder_): os.makedirs(folder_)

            file = "/home/juju/gisco/accessibility/euro_access_"+service+"_"+year+"_"+resolution+"m.tif"
            gridtiler_raster.tiling_raster(
                {
                    service+"_"+year+"_1": {"file":file, "band":1},
                    service+"_"+year+"_a3": {"file":file, "band":2},
                },
                folder_,
                crs="EPSG:3035",
                tile_size_cell=256,
                format="parquet",
                num_processors_to_use = 10,
                )


combine("1000")

