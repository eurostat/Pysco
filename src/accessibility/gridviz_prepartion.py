from pygridmap import gridtiler_raster
import sys
import os
from rasterio.enums import Resampling

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import combine_geotiffs, resample_geotiff_aligned


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
    combine_geotiffs(tiffs, folder+resolution+".tif", compress="deflate")



def aggregate():
    resolution = 1000
    for f in [2, 5, 10, 20, 50, 100]:
        print(resolution, f)
        resample_geotiff_aligned(folder+str(resolution)+".tif", folder+str(f*resolution)+".tif", f*resolution, Resampling.average)

    resolution = 100
    for f in [2, 5]:
        print(resolution, f)
        resample_geotiff_aligned(folder+str(resolution)+".tif", folder+str(f*resolution)+".tif", f*resolution, Resampling.average)





def tiling():

    for f in [1,2,5, 10,20,50, 100,200,500, 1000]:
        resolution = 100 * f

        # make folder for resolution
        folder_ = folder+"tiles/"+str(resolution)+"/"
        if not os.path.exists(folder_): os.makedirs(folder_)

        # prepare dict for geotiff bands
        dict = {}
        band = 0
        for service in ["education", "healthcare"]:
            for year in ["2020", "2023"]:
                for indic in ["1", "a3"]:
                    code = service+"_"+year+"_"+indic
                    dict[code] = {"file":folder+str(resolution)+".tif", "band":band}
                    band +=1
        print(dict)

        # launch tiling
        print("tiling for resolution", resolution)
        gridtiler_raster.tiling_raster(
            dict,
            folder_,
            crs="EPSG:3035",
            tile_size_cell = 256,
            format="parquet",
            num_processors_to_use = 10,
            )


#print("combine geotiffs")
combine("1000")
combine("100")

print("aggregate")
aggregate()
#TODO fails for 200m aggregation


