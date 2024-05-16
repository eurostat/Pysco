import os
from gridtiler import grid_tiling
from gridaggregator import grid_aggregation
from gridtransformation import grid_transformation


#working folder
folder = "/home/juju/Bureau/tmp_bdem_tiling_prep/"
if not os.path.exists(folder): os.makedirs(folder)



#input file preparation

#set cell x,y from its grid_id
def position_fun(c):
    a = c['GRD_ID'].split("N")[1].split("E")
    c["x"] = int(a[1])
    c["y"] = int(a[0])
    del c['GRD_ID']

grid_transformation("/home/juju/gisco/building_demography/building_demography.csv", position_fun, folder + '100.csv')



#aggregation
for a in [2,5,10,20,50,100,200,500]:
    print("aggregation to", a*100, "m")
    grid_aggregation(folder+"100.csv", 100, folder+str(a*100)+'.csv', a)


#tiling
for a in [1,2,5,10,20,50,100,200,500]:
    print("tiling for resolution", a*100, "m")
    grid_tiling(
        folder+str(a*100)+'.csv',
        '/home/juju/workspace/BuildingDemography/pub/tiles/',
        100,
        #tile_size_cell = 128,
        x_origin = 2500000,
        y_origin = 1000000,
        crs = "EPSG:3035"
    )
