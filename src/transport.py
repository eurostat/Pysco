import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

# df = pd.read_csv('your_csv_file.csv')
df = pd.read_excel('your_xls_file.xls')

geometries = []
for index, row in df.iterrows():
    point1 = (row['x1'], row['y1'])
    point2 = (row['x2'], row['y2'])
    line = LineString([point1, point2])
    geometries.append(line)

gdf = gpd.GeoDataFrame(df, geometry=geometries)
gdf.to_file('output_dataset.gpkg', driver='GPKG')
