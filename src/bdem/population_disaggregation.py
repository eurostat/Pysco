import fiona
from fiona.crs import CRS
from datetime import datetime

import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from utils.featureutils import loadFeatures, keep_attributes, get_schema_from_feature




nb_decimal = 2

#define budem tile to process
x_min = 4000000; y_min = 2500000 #LU

#define country list
cnt = ["FR", "NL", "PL", "IT", "LU"]

#load 100m budem cells in tile
print(datetime.now(), x_min, y_min, "load budem cells")
budem_grid = loadFeatures("/home/juju/Bureau/budem_test.gpkg")
#budem_grid = loadFeatures("/home/juju/gisco/building_demography/out_partition/eurobudem_100m_"+str(x_min)+"_"+str(y_min)+".gpkg")
print(datetime.now(), x_min, y_min, len(budem_grid), "budem cells loaded")
if(len(budem_grid)==0): exit

#filter population cell data
for c in budem_grid:
    keep_attributes(c, ["GRD_ID", "residential_floor_area"])
    #extract LLC position
    a = c['GRD_ID'].split('mN')[1].split('E')
    c['X_LLC'] = int(a[1])
    c['Y_LLC'] = int(a[0])
    #initialise population
    c['TOT_P_2021'] = 0

#load 1000m population cells in tile
print(datetime.now(), x_min, y_min, "load 1000m population cells")
pop_grid = loadFeatures("/home/juju/Bureau/pop_test.gpkg", bbox=[x_min, y_min, x_min+500000, y_min+500000])
#pop_grid = loadFeatures("/home/juju/geodata/grids/grid_1km_surf.gpkg", bbox=[x_min, y_min, x_min+500000, y_min+500000])
print(datetime.now(), x_min, y_min, len(pop_grid), "pop cells loaded")
pop_grid = [pc for pc in pop_grid if pc["NUTS2021_0"] in cnt]
print(datetime.now(), x_min, y_min, len(pop_grid), "pop cells, after filtering on " + str(cnt))

#filter population cell data
for pc in pop_grid:
    keep_attributes(pc, ["Y_LLC", "X_LLC", "TOT_P_2021"])



#index 100m cells by x and then y
index = {}
for c in budem_grid:
    x = c["X_LLC"]
    if not x in index: index[x]={}
    index[x][c["Y_LLC"]] = c


#for each 1000m population cell
for pc in pop_grid:

    #skip non populated cell
    pop = pc["TOT_P_2021"]
    if pop == None or pop == "" or pop == 0: continue

    #get cell position
    x = pc["X_LLC"]
    y = pc["Y_LLC"]

    #get 100m cells inside 1000m cell using index
    c100m = []
    for i in range(10):
        x_ = x+i*100
        if not x_ in index: continue
        a = index[x_]
        for j in range(10):
            y_ = y+j*100
            if not y_ in a: continue
            cbu = a[y_]
            #exclude the ones without residential area
            if cbu["residential_floor_area"]==0: continue
            c100m.append(cbu)

    if len(c100m)==0:
        print("found population cell without residential area around",x,y)
        #TODO assign population equally to all cells ? or a central one ?
        continue

    #compute total bu_res
    bu_res = 0
    for cbu in c100m: bu_res+=cbu["residential_floor_area"]

    if bu_res == 0:
        print("Unexpectect null building residence area around",x,y)
        continue

    #assign 100m population as pop*bu_res/tot_bu_res
    for cbu in c100m: cbu["TOT_P_2021"] = round(pop * cbu["residential_floor_area"] / bu_res, nb_decimal)


print(datetime.now(), "save as GPKG")
for cell in budem_grid: cell["geometry"] = None
schema = get_schema_from_feature(budem_grid[0])
out = fiona.open("/home/juju/Bureau/test.gpkg", 'w', driver='GPKG', crs=CRS.from_epsg(3035), schema=schema)
out.writerecords(budem_grid)
