import geopandas as gpd
from datetime import datetime
from geomutils import decompose_line

folder = '/home/juju/gisco/OME2_analysis/'
file_path = '/home/juju/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg'
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

intersection_points = []
for buffer in gdf:
    buffer = buffer.exterior
    print(datetime.now(),"***", buffer.bounds)
    print(datetime.now(), "load road sections")
    rn = gpd.read_file(file_path, layer='tn_road_link', bbox=buffer.bounds)
    print(str(len(rn)) + " road sections")
    rn = rn['geometry']
    print(datetime.now(), " get intersecting road sections")
    rni = rn[rn.geometry.intersects(buffer)]
    rn = rni
    print(str(len(rni)) + " road sections intersecting")

    print(datetime.now(), " get intersection points")
    for line in rn.geometry:
        intersection = line.intersection(buffer)
        if intersection.geom_type == 'Point':
            intersection_points.append(intersection)
        elif intersection.geom_type == 'MultiPoint':
            intersection_points.extend(list(intersection.geoms))

    print(len(intersection_points))

print(datetime.now(), "save")
gdf = gpd.GeoDataFrame(geometry=intersection_points)
gdf.crs = 'EPSG:3035'
gdf.to_file(folder+"xborder_nodes.gpkg", driver="GPKG")
