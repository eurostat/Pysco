
#TODO
#rely on csv
#

from pygridmap import gridtiler
from datetime import datetime

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.gridutils import get_cell_xy_from_id

transform = False
aggregation = True
tiling = False

input_file = "/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.csv"
tmp = "tmp/census2021_tiling/"
os.makedirs(tmp, exist_ok=True)


def transform_fun(c):
    #print(c.keys())
    #['fid', 'GRD_ID',
    # 'T',
    # 'M', 'F',
    # 'Y_LT15', 'Y_1564', 'Y_GE65',
    # 'EMP',
    # 'NAT', 'EU_OTH', 'OTH',
    # 'SAME', 'CHG_IN', 'CHG_OUT',
    # 'LAND_SURFACE', 'POPULATED',
    # 'T_CI',
    # 'M_CI', 'F_CI',
    # 'Y_LT15_CI', 'Y_1564_CI', 'Y_GE65_CI',
    # 'EMP_CI',
    # 'NAT_CI', 'EU_OTH_CI', 'OTH_CI',
    # 'SAME_CI', 'CHG_IN_CI', 'CHG_OUT_CI'])

    # filter out cells with no population
    t = c["T"]
    if t=="0" or t=="" or t == None: return False

    del c["fid"]
    del c["POPULATED"]
    del c["LAND_SURFACE"]

    #get x and y
    [x, y] = get_cell_xy_from_id(c['GRD_ID'])
    c["x"] = x
    c["y"] = y
    del c['GRD_ID']

    # address confidentiality. Encode it at value level: -1
    for p in "T","M","F","Y_LT15","Y_1564","Y_GE65","EMP","NAT","EU_OTH","OTH","SAME","CHG_IN","CHG_OUT":
        pci = c[p+"_CI"]
        if pci == "-9999" or pci == "-9986" or pci == "0":
            c[p] = -1
        elif pci != "": print(p, pci)
        del c[p+"_CI"]

    c["NB"] = 1

    # necessary ?
    #remove zeros
    #for p in "T","M","F","Y_LT15","Y_1564","Y_GE65","EMP","NAT","EU_OTH","OTH","SAME","CHG_IN","CHG_OUT":
    #    v = c[p]
    #    if v == "0": c[p] = ""

    #print(c)


#apply transform
if transform:
    print("transform")
    gridtiler.grid_transformation(input_file=input_file, output_file=tmp+"1000.csv", function=transform_fun)





#aggregation
if aggregation:

    #aggregation function
    def aggFun(values, _):
        return 0

    af = {}
    for p in "T","M","F","Y_LT15","Y_1564","Y_GE65","EMP","NAT","EU_OTH","OTH","SAME","CHG_IN","CHG_OUT":
        af[p] = aggFun

    #launch aggregation
    for a in [2,5,10]:
        print(datetime.now(), "aggregation to", a*1000, "m")
        gridtiler.grid_aggregation(input_file=tmp+"1000.csv", resolution=1000, output_file=tmp+str(a*1000)+".csv", a=a, aggregation_fun = af)
    for a in [2,5,10]:
        print(datetime.now(), "aggregation to", a*10000, "m")
        gridtiler.grid_aggregation(input_file=tmp+"10000.csv", resolution=10000, output_file=tmp+str(a*10000)+".csv", a=a, aggregation_fun = af)



#tiling
if tiling:
    for resolution in [1000, 2000, 5000, 10000, 20000, 50000, 100000]:
        print("tiling for resolution", resolution)

        #create output folder
        out_folder = folder + 'out/' + str(resolution)
        if not os.path.exists(folder): os.makedirs(folder)

        gridtiler.grid_tiling(
            folder+"out/ESTAT_Census_2021_V2_"+str(resolution)+'.csv',
            out_folder,
            resolution,
            tile_size_cell = 256,
            x_origin = 0,
            y_origin = 0,
            crs = "EPSG:3035",
            format = "parquet"
        )



"""
from pygridmap import gridtiler_raster
import sys
import os
from rasterio.enums import Resampling
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import resample_geotiff_aligned


f0 = "/home/juju/geodata/census/2021/"
tmp = "tmp/census2021_tiling/"
resolutions = [ 100000, 50000, 20000, 10000, 5000, 2000, 1000 ]

aggregate = False
tiling = True


os.makedirs(tmp, exist_ok=True)

# aggregate at various resolutions - sum
if aggregate:
    print(datetime.now(), "aggregate")
    for p in "T","M","F","Y_LT15","Y_1564","Y_GE65","EMP","NAT","EU_OTH","OTH","SAME","CHG_IN","CHG_OUT":
        for resolution in resolutions:
            print(datetime.now(), p, resolution)
            resample_geotiff_aligned(f0 + "ESTAT_OBS-VALUE-"+p+"_2021_V2.tiff", tmp+str(resolution)+"_"+p+".tif", resolution, Resampling.sum)


parts = {
    "total" : ["T"],
    "sex" : ["T", "M", "F"],
    "age" : ["T", "Y_LT15","Y_1564","Y_GE65"],
    "emp" : ["T", "EMP"],
    "mob" : ["T","SAME","CHG_IN","CHG_OUT"],
    "pob" : ["T", "NAT","EU_OTH","OTH"],
    "all" : ["T","M","F","Y_LT15","Y_1564","Y_GE65","EMP","NAT","EU_OTH","OTH","SAME","CHG_IN","CHG_OUT"]
}


if tiling:
    print(datetime.now(), "tiling")
    for resolution in resolutions:
        for part in parts:
            ps = parts[part]
            print(datetime.now(), "Tiling", resolution, part)

            # make folder for resolution
            folder_ = tmp+"tiles_"+part+"/"+str(resolution)+"/"
            os.makedirs(folder_, exist_ok=True)

            # prepare dict for geotiff bands
            dict = {}
            for p in ps:
                dict[p] = {"file":tmp+str(resolution)+"_"+p+".tif", "band":1}

            # launch tiling
            gridtiler_raster.tiling_raster(
                dict,
                folder_,
                crs="EPSG:3035",
                tile_size_cell = 256 if p=="all" else 512,
                format="parquet",
                num_processors_to_use = 10,
                #modif_fun = round,
                )
"""

