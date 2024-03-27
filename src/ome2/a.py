import geopandas as gpd
from shapely.geometry import box

file_path = '/home/juju/Bureau/gisco/geodata/OME2_HVLSP_v1/gpkg/ome2_hvlsp_v1.1.1.gpkg'
minx = 2720000
maxx = 2730000
miny = 4080000
maxy = 4090000
bbox = box(minx, miny, maxx, maxy)

print("loading...")
gdf = gpd.read_file(file_path, bbox=bbox) #, layer='batiment'

print(gdf.dtypes)
print(gdf.shape)
