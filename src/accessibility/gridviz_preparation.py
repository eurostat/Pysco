# prepare accessibility grid for gridviz mapping


from pygridmap import gridtiler_raster
import sys
import os
from rasterio.enums import Resampling

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import combine_geotiffs, resample_geotiff_aligned



f0 = "/home/juju/gisco/accessibility/"
folder = f0 + "gridviz/"
if not os.path.exists(folder): os.makedirs(folder)


# combine all necessary data into a single geotiffs
def combine(resolution):
    for service in ["education", "healthcare"]:
        # make list of files to combine
        tiffs = []
        for year in ["2020", "2023"]:
            tiffs.append( f0 + "euro_access_"+service+"_"+year+"_"+resolution+"m.tif" )
        # combine files
        combine_geotiffs(tiffs, folder+service+"_"+resolution+".tif", compress="deflate")


# aggregate at various resolutions - average
def aggregate():
    for service in ["education", "healthcare"]:

        resolution = 1000
        for f in [2, 5, 10, 20, 50, 100]:
            print(service, resolution, f)
            resample_geotiff_aligned(folder+service+"_"+str(resolution)+".tif", folder+service+"_"+str(f*resolution)+".tif", f*resolution, Resampling.average)

        resolution = 100
        for f in [2, 5]:
            print(service, resolution, f)
            resample_geotiff_aligned(folder+service+"_"+str(resolution)+".tif", folder+service+"_"+str(f*resolution)+".tif", f*resolution, Resampling.average)




#TODO: add also population figures !
def tiling():

    for f in [ 1000, 500, 200, 50, 20, 10, 5, 2, 1 ]:
        resolution = 100 * f

        for service in ["education", "healthcare"]:

            print("Tiling", service, resolution)

            # make folder for resolution
            folder_ = folder+"tiles/"+service+"_"+str(resolution)+"/"
            if not os.path.exists(folder_): os.makedirs(folder_)

            # prepare dict for geotiff bands
            dict = {}
            band = 1
            for year in ["2020", "2023"]:
                for indic in ["1", "a3"]:
                    dict[indic + "_" + year] = {"file":folder+service+"_"+str(resolution)+".tif", "band":band}
                    band +=1

            # launch tiling
            gridtiler_raster.tiling_raster(
                dict,
                folder_,
                crs="EPSG:3035",
                tile_size_cell = 256,
                format="parquet",
                num_processors_to_use = 10,
                )


#print("combine geotiffs")
#combine("1000")
#combine("100")

#print("aggregate")
#aggregate()

print("tiling")
tiling()

