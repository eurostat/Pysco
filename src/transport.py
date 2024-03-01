import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

file = "/home/juju/Bureau/gisco/rail_rinf/NET_SEGMENTS_EU_EFTA.xlsx"
outFolder = '/home/juju/Bureau/gisco/rail_rinf/'

print("Start")

# df = pd.read_csv('jhbb.csv')
df = pd.read_excel(file)
print(str(len(df)) + " segments loaded")

geometries = []
for index, row in df.iterrows():
    try:
        # print(row['Fromlongitude'], row['Fromlatitude'], row['Tolongitude'], row['Tolatitude'])
        point1 = (row['Fromlongitude'], row['Fromlatitude'])
        point2 = (row['Tolongitude'], row['Tolatitude'])
        geometries.append(LineString([point1, point2]))
    except Exception as e:
        print("An error occurred for segment "+row["Network segment identifier"]+":", e)
        geometries.append(LineString([]))

print("Save as GPKG file")
gdf = gpd.GeoDataFrame(df, geometry=geometries)
gdf.to_file(outFolder+'out.gpkg', driver='GPKG', crs="EPSG:4258")

print("End")
