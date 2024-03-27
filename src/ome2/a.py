import geopandas as gpd
from shapely.geometry import box

# reproject
# ogr2ogr -f GPKG -t_srs EPSG:3035 ome2.gpkg ome2_hvlsp_v1.1.1.gpkg

file_path = '/home/juju/Bureau/gisco/geodata/OME2_HVLSP_v1/gpkg/ome2_hvlsp_v1.1.1.gpkg'
out_folder = '/home/juju/Bureau/gisco/OME2_analysis/'
minx = 2720000
maxx = 2730000
miny = 4080000
maxy = 4090000
bbox = box(minx, miny, maxx, maxy)

print("loading...")
gdf = gpd.read_file(file_path, bbox=bbox) #, layer='batiment'

print(gdf.dtypes)
print(gdf.shape)
