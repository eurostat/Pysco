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
        out_folder = rep+'/tiled/' + str(resolution)
        if not os.path.exists(out_folder): os.makedirs(out_folder)

        grid_tiling(
            rep+"EU_"+str(resolution)+'.csv',
            out_folder,
            resolution,
            #tile_size_cell = 128,
            #x_origin = 2500000,
            #y_origin = 1000000,
            crs = "EPSG:3035"
        )




# tiling function, via gridtiler
def tiling(a):
    subprocess.run(
        [
            "gridtiler",
            "-i",
            rep+"EU.csv",
            "-r",
            "1000",
            "-c",
            "3035",
            "-x",
            "3800000",
            "-y",
            "2500000",
            "-p",
            "const a = c.SPATIAL.split('N')[1].split('E'); return { x:a[1],y:a[0] };",
            "-m",
            "delete c.SPATIAL",
            "-a",
            str(a),
            "-o",
            rep+"tiled_"+format+"/"
            + str(a * 1000)
            + "m/",
            "-e",
            "csv",
        ]
    )

# launch tiling
#for a in [1,2,5,10,20,50,100]: tiling(a)















# load all country files into a single data frame
def load(cc, nb=0):
    if (nb==0):
        return pd.read_csv(rep + cc+"_in.csv", sep=',' if (cc=="LV") else ';')

    # load each file
    dfs = []
    for i in range(1, nb + 1):
        file_path = rep + cc + "_in_" + str(i) + ".csv"
        dfs.append(pd.read_csv(file_path, sep=',' if (cc=="LV") else ';'))
    return pd.concat(dfs, ignore_index=True)


# prepare country output csv file
def prepare(cc, nb=0):
    print(cc)
    df = load(cc, nb)

    df = df[["STAT","SPATIAL","OBS_VALUE"]]
    df['SPATIAL'] = df['SPATIAL'].str[3:]

    #print(df['STAT'].unique())
    # ['CHG_IN' 'CHG_OUT' 'EMP' 'EU_OTH' 'F' 'M' 'NAT' 'OTH' 'SAME' 'T' 'Y_GE65' 'Y_LT15' 'Y15-64']

    df = df.pivot(index='SPATIAL', columns='STAT', values='OBS_VALUE')

    df['cc'] = cc
 
    #TODO remove the ones with SPATIAL="unlocated"

    #print(df)

    df.to_csv(rep+cc+".csv", index=True)


# merge country files NL.csv into a single EU.csv file
def merge(ccs):
    print('merge '+str(ccs))
    dfs = [pd.read_csv(rep+cc+".csv") for cc in ccs]
    merged_df = pd.concat(dfs, axis=0, ignore_index=True)
    merged_df.to_csv(rep+"EU.csv", index=False)
   



# prepare
#prepare("AT")
#prepare("NL")
#prepare("LV")
#prepare("DK", 5)
#prepare("SK",5)


# merge
#merge(['LV','NL','AT', 'SK', 'DK'])

