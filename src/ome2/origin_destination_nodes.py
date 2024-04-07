import geopandas as gpd
from shapely.geometry import LineString
from datetime import datetime
from geomutils import decompose_line

folder = '/home/juju/Bureau/gisco/OME2_analysis/'
file_path = '/home/juju/Bureau/gisco/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg'
buffer_distance = 1000

print(datetime.now(), "load boundaries")
gdf = gpd.read_file(folder+"bnd.gpkg")
print(str(len(gdf)) + " boundaries")

print(datetime.now(), "simplify boundaries")
gdf['geometry'] = gdf['geometry'].simplify(100)

print(datetime.now(), "decompose boundaries")
nb_vertices = 80
decomposed_segments = gdf['geometry'].apply(lambda line:decompose_line(line,nb_vertices))
flat_segments = [segment for sublist in decomposed_segments for segment in sublist]
gdf = gpd.GeoDataFrame(geometry=flat_segments)
gdf.crs = 'EPSG:3035'
#gdf.to_file(folder+"bnd_pieces.gpkg", driver="GPKG")
print(str(len(gdf)) + " decomposed boundaries")

print(datetime.now(), "compute buffers")
gdf = gdf['geometry'].buffer(buffer_distance, resolution=2)
#gdf.to_file(folder+"buffers.gpkg", driver="GPKG")

for buffer in gdf:
    buffer = buffer.exterior
    print(datetime.now(),"***", buffer.bounds)
    print(datetime.now(), "load road sections")
    rn = gpd.read_file(file_path, layer='tn_road_link', bbox=buffer.bounds)
    print(str(len(rn)) + " road sections")
    rn = rn['geometry']
    print(datetime.now(), " get intersecting road sections")
    rni = rn[rn.geometry.intersects(buffer)]
    print(str(len(rni)) + " road sections intersecting")
