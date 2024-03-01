import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

file = "/home/juju/Bureau/gisco/rail_rinf/NET_SEGMENTS_EU_EFTA.xlsx"
#file = "/home/juju/Bureau/gisco/rail_rinf/RINF_EU_EFTA.xlsx"
outFolder = '/home/juju/Bureau/gisco/rail_rinf/'

print("Load data from "+file)
df = pd.read_excel(file)
print(str(len(df)) + " segments loaded")

print("Make features")
geometries = []
for index, row in df.iterrows():
    try:
        geometries.append(LineString([(row['Fromlongitude'], row['Fromlatitude']), (row['Tolongitude'], row['Tolatitude'])]))
        #geometries.append(LineString([(row['Point Start Longitude'], row['Point Start Latitude']), (row['Point End Longitude'], row['Point End Latitude'])]))
    except Exception as e:
        print("Problem with segment "+row["Network segment identifier"]+":", e)
        geometries.append(LineString([]))

print("Save as GPKG file")
gdf = gpd.GeoDataFrame(df, geometry=geometries)
gdf.to_file(outFolder+'out.gpkg', driver='GPKG', crs="EPSG:4258")
#gdf.to_file(outFolder+'out_rinf.gpkg', driver='GPKG', crs="EPSG:4258")
