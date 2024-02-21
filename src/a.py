import pandas as pd
import subprocess



rep="/home/juju/Bureau/gisco/grid_pop_c2021/"


def load(cc, nb=0):
    if (nb==0):
        return pd.read_csv(rep + cc+"_in.csv", sep=',' if (cc=="LV") else ';')

    # load each file
    dfs = []
    for i in range(1, nb + 1):
        file_path = rep + cc+"_in_"+i  + ".csv"
        dfs.append(pd.read_csv(file_path, sep=',' if (cc=="LV") else ';'))
    return pd.concat(dfs, ignore_index=True)



def prepare(cc):
    print(cc)
    df = load(cc)

    df = df[["STAT","SPATIAL","OBS_VALUE"]]
    df['SPATIAL'] = df['SPATIAL'].str[3:]

    #print(df['STAT'].unique())
    # ['CHG_IN' 'CHG_OUT' 'EMP' 'EU_OTH' 'F' 'M' 'NAT' 'OTH' 'SAME' 'T' 'Y_GE65' 'Y_LT15' 'Y15-64']

    df = df.pivot(index='SPATIAL', columns='STAT', values='OBS_VALUE')

    df['cc'] = cc

    #print(df)

    df.to_csv(rep+cc+".csv", index=True)



def merge(ccs):
    print('merge '+str(ccs))
    dfs = [pd.read_csv(rep+cc+".csv") for cc in ccs]
    merged_df = pd.concat(dfs, axis=0, ignore_index=True)
    merged_df.to_csv(rep+"EU.csv", index=False)
   



# prepare
prepare("AT")
#prepare("NL")
#prepare("LV")
#prepare("DK",5)
#prepare("SK",5)


# merge
#merge(['LV','NL','AT'])



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
            rep+"tiled/"
            + str(a * 1000)
            + "m/",
            "-e",
            "csv",
        ]
    )

# launch tiling
#for a in [1,2,5,10,20,50,100]: tiling(a)
