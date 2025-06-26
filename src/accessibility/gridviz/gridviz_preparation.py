# prepare accessibility grid for gridviz mapping


from pygridmap import gridtiler_raster
import sys
import os
from rasterio.enums import Resampling

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import resample_geotiff_aligned



f0 = "/home/juju/gisco/accessibility/"
folder = f0 + "gridviz/"
if not os.path.exists(folder): os.makedirs(folder)

folder_pop_tiff = "/home/juju/geodata/census/2021/aggregated_tiff/"


# aggregate at various resolutions - average
def aggregate():

    for year in ["2023", "2020"]:
        for service in ["education", "healthcare"]:

            for resolution in [200, 500]:
                print(service, year, resolution)
                inp = "euro_access_"+service+"_"+year+"_100m.tif"
                resample_geotiff_aligned(inp, folder+service+"_"+str(resolution)+".tif", resolution, Resampling.average)

            print(service, year, 1000)
            resample_geotiff_aligned(folder+service+"_500.tif", folder+service+"_1000.tif", 1000, Resampling.average)

            for resolution in [2000, 5000, 10000]:
                print(service, year, resolution)
                resample_geotiff_aligned(folder+service+"_1000.tif", folder+service+"_"+str(resolution)+".tif", resolution, Resampling.average)

            for resolution in [20000, 50000, 100000]:
                print(service, year, resolution)
                resample_geotiff_aligned(folder+service+"_10000.tif", folder+service+"_"+str(resolution)+".tif", resolution, Resampling.average)


def tiling():

    for f in [ 1000, 500, 200, 100, 50, 20, 10, 5, 2, 1 ]: #, 1
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
                    dict["dt_" + indic + "_" + year] = {"file":folder+service+"_"+str(resolution)+".tif", "band":band}
                    band +=1
                dict["POP_2021"] = { "file":folder_pop_tiff+"pop_2021_"+str(resolution)+".tif", "band":1 }

            # launch tiling
            gridtiler_raster.tiling_raster(
                dict,
                folder_,
                crs="EPSG:3035",
                tile_size_cell = 256,
                format="parquet",
                num_processors_to_use = 10,
                )


print("aggregate")
aggregate()

#print("tiling")
#tiling()

