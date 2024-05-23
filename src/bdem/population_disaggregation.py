from datetime import datetime
import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from utils.featureutils import loadFeatures


#define budem tile to process
x_min = 4000000; y_min = 2500000 #LU

#define country list
cnt = ["FR", "NL", "PL", "IT", "LU"]

#load 100m budem cells in tile
print(datetime.now(), x_min, y_min, "load budem cells")
budem = loadFeatures("/home/juju/gisco/building_demography/out_partition/eurobudem_100m_"+str(x_min)+"_"+str(y_min)+".gpkg")
print(datetime.now(), x_min, y_min, len(budem), "budem cells loaded")
if(len(budem)==0): exit

#load 1000m population cells in tile
print(datetime.now(), x_min, y_min, "load 1000m population cells")
pop = loadFeatures("/home/juju/geodata/grids/grid_1km_surf.gpkg", bbox=[x_min, y_min, x_min+500000, y_min+500000])
print(datetime.now(), x_min, y_min, len(pop), "pop cells loaded")

#filter pop: countries and keep only cell_id,pop

#index 100m cells

#for each 1000m population cell with non-null population

    #get 100m cells
    #compute total bu_res
    #for each 100m cell
        #assign 100m population as pop*bu_res/tot_bu_res

