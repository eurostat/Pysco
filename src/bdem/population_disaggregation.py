import fiona
from fiona.crs import CRS
from datetime import datetime
import os

import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from utils.featureutils import loadFeatures, keep_attributes, get_schema_from_feature



def disaggregate_population_100m(x_min, y_min, nb_decimal = 2, cnt_codes = []):

    input_budem_file = "/home/juju/gisco/building_demography/out_partition/eurobudem_100m_"+str(x_min)+"_"+str(y_min)+".gpkg"
    if not os.path.isfile(input_budem_file): return

    #load 100m budem cells in tile
    print(datetime.now(), x_min, y_min, "load 100m budem cells")
    budem_grid = loadFeatures(input_budem_file)
    print(datetime.now(), x_min, y_min, len(budem_grid), "budem cells loaded")
    if(len(budem_grid)==0): return

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
    pop_grid = loadFeatures("/home/juju/geodata/grids/grid_1km_surf.gpkg", bbox=[x_min, y_min, x_min+500000, y_min+500000])
    print(datetime.now(), x_min, y_min, len(pop_grid), "pop cells loaded")
    pop_grid = [pc for pc in pop_grid if pc["NUTS2021_0"] in cnt_codes]
    print(datetime.now(), x_min, y_min, len(pop_grid), "pop cells, after filtering on " + str(cnt_codes))

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
            print(datetime.now(), x_min, y_min, "found population cell without residential area around",x,y, "population lost:", pop)
            #TODO assign population equally to all cells ? or a central one ?
            continue

        #compute total bu_res
        bu_res = 0
        for cbu in c100m: bu_res+=cbu["residential_floor_area"]

        if bu_res == 0:
            print(datetime.now(), x_min, y_min, "Unexpectect null building residence area around",x,y)
            continue

        #assign 100m population as pop*bu_res/tot_bu_res
        for cbu in c100m: cbu["TOT_P_2021"] = round(pop * cbu["residential_floor_area"] / bu_res, nb_decimal)

    print(datetime.now(), x_min, y_min, "save as GPKG")

    #build output data
    outd = []
    for cell in budem_grid:
        o = {"properties":{}}
        x = cell["X_LLC"]; y = cell["Y_LLC"]
        del cell["X_LLC"]; del cell["Y_LLC"]
        for k in cell: o["properties"][k] = cell[k]
        o["geometry"] = {'type': 'Polygon', 'coordinates': [[(x,y),(x+100,y),(x+100,y+100),(x,y+100),(x,y)]]}
        outd.append(o)

    #save it as gpkg
    schema = get_schema_from_feature(outd[0])
    outf = fiona.open("/home/juju/gisco/grid_pop_100m/pop_2021_100m_"+str(x_min)+"_"+str(y_min)+".gpkg", 'w', driver='GPKG', crs=CRS.from_epsg(3035), schema=schema)
    outf.writerecords(outd)


#TODO parallel
#define country list
cnt_codes = ["FR", "NL", "PL", "IT", "LU"]
for x_min in range(3000000, 5500000, 500000):
    for y_min in range(1000000, 4000000, 500000):
        print(datetime.now(), x_min, y_min, "disaggregation ************")
        disaggregate_population_100m(x_min, y_min, cnt_codes=cnt_codes)
