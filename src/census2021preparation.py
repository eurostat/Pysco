import pandas as pd
import subprocess
import os
import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from gridtiler.gridtiler import grid_aggregation,grid_tiling,grid_transformation

prepare = True
transform = True
aggregation = True
tiling = True
format = "parquet"

#the working folder
rep="/home/juju/gisco/grid_pop_c2021/"

if prepare:
    #the input files
    inrep = rep+"input_data/"
    input_files = os.listdir(inrep)

    #load files in dataframes
    dfs = []
    for file in input_files:

        cc = file[14:16]
        #if cc!="AT": continue

        print(file)

        #load data
        df = pd.read_csv(inrep + file, sep=';')

        #select colmuns
        df = df[["STAT","SPATIAL","OBS_VALUE"]]

        #remove country code from grid id
        df['SPATIAL'] = df['SPATIAL'].str[3:]

        #remove unallocated rows
        df = df[df['SPATIAL'] != 'unallocated']
        #un_i = df[df['SPATIAL'] == 'unallocated'].index
        #df = df.drop(un_i)

        #pivot
        df = df.pivot(index='SPATIAL', columns='STAT', values='OBS_VALUE')

        #add column with country code
        df['cc'] = cc

        dfs.append(df)

    #merge file dataframes into a single one
    print("merge")
    df = pd.concat(dfs, ignore_index=False)

    #TODO aggregate by cell id

    #remove unpopulated cells
    df = df[df['T'] != 0]

    print(df)

    #save
    print("save")
    df.to_csv(rep+"EU.csv", index=True)



if transform:
    print("transform")
    def fun(c):
        a = c['SPATIAL'].split("N")[1].split("E")
        c["x"] = int(a[1])
        c["y"] = int(a[0])
        del c['SPATIAL']
        del c['cc']
    #transform
    grid_transformation(rep+"EU.csv", fun, rep+"EU_1000.csv")





#aggregation
if aggregation:
    for a in [2,5,10]:
        print("aggregation to", a*1000, "m")
        grid_aggregation(rep+"EU_1000.csv", 1000, rep+"EU_"+str(a*1000)+'.csv', a)
    for a in [2,5,10]:
        print("aggregation to", a*10000, "m")
        grid_aggregation(rep+"EU_10000.csv", 10000, rep+"EU_"+str(a*10000)+'.csv', a)


#TODO

#tiling
if tiling:
    for resolution in [1000, 2000, 5000, 10000, 20000, 50000, 100000]:
        print("tiling for resolution", resolution)
        
        #create output folder
        out_folder = rep+'/tiled_'+format+'/' + str(resolution)
        if not os.path.exists(out_folder): os.makedirs(out_folder)

        grid_tiling(
            rep+"EU_"+str(resolution)+'.csv',
            out_folder,
            resolution,
            #tile_size_cell = 128,
            #x_origin = 2500000,
            #y_origin = 1000000,
            crs = "EPSG:3035",
            format = format
        )

