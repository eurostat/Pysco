import geopandas as gpd
import pandas as pd

print("start")

base = "L:/archive/road-network/raw-deliveries/2021/EETN2021/EU/eur2021_12_000/shpd/mn/"
shp_files = [
    base + "fra/f10/fraf10___________nw.shp",
    base + "fra/f11/fraf11___________nw.shp"
]

gpdfs = []
for file in shp_files:
    print(file)
    gpdf = gpd.read_file(file)
    print(len(gpdf))
    gpdfs.append(gpdf)
merged_gpdf = gpd.GeoDataFrame(pd.concat(gpdfs, ignore_index=True))

merged_gpdf.to_file('H:/desktop/mn.gpkg', driver='GPKG')
