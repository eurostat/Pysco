import geopandas as gpd
from shapely.geometry import box

# reproject
# ogr2ogr -f GPKG -t_srs EPSG:3035 ome2.gpkg ome2_hvlsp_v1.1.1.gpkg

file_path = '/home/juju/Bureau/gisco/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg'
out_folder = '/home/juju/Bureau/gisco/OME2_analysis/'
minx = 3900000
maxx = 3960000
miny = 3000000
maxy = 3060000
bbox = box(minx, miny, maxx, maxy)

print("loading")
gdf = gpd.read_file(file_path, layer='tn_road_link', bbox=bbox)

print(len(gdf))
#print(gdf.bounds)
#print(gdf.dtypes)
#print(gdf.shape)

print("save")
gdf.to_file(out_folder+"test.gpkg", driver="GPKG")
