import pandas as pd

file_path = '/home/juju/Bureau/gisco/grid_pop_c2021/NL_2021_0000_V0002.csv'
df = pd.read_csv(file_path, sep=';')

df = df[["STAT","SPATIAL","OBS_VALUE"]]

#print(df['STAT'].unique())
# ['CHG_IN' 'CHG_OUT' 'EMP' 'EU_OTH' 'F' 'M' 'NAT' 'OTH' 'SAME' 'T' 'Y_GE65' 'Y_LT15' 'Y15-64']

df = df.pivot(index='SPATIAL', columns='STAT', values='OBS_VALUE')

print(df)
