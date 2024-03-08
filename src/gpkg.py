import geopandas as gpd
from shapely.geometry import box

file_path = 'data/90.gpkg'
minx = 2720000
maxx = 2730000
miny = 4080000
maxy = 4090000
bbox = box(minx, miny, maxx, maxy)

print("loading...")
gdf = gpd.read_file(file_path, layer='batiment', bbox=bbox)

print(gdf.dtypes)
print(gdf.shape)
