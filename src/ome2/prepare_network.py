import geopandas as gpd
from shapely.geometry import LineString
from datetime import datetime
from ome2utils import ome2_filter_road_links, road_link_speed_kmh

out_folder = '/home/juju/gisco/OME2_analysis/'

print(datetime.now(), "loading")
size = 60000
gdf = gpd.read_file(out_folder+"test_"+str(size)+".gpkg")
print(str(len(gdf)) + " links")
gdf = ome2_filter_road_links(gdf)
print(str(len(gdf)) + " links")
#print(gdf.dtypes)

#compute speed
gdf['speed_kmh'] = gdf.apply(road_link_speed_kmh, axis=1)

#keep only speed column
geometry = gdf.geometry
selected_column = gdf['speed_kmh']
gdf = gpd.GeoDataFrame(geometry=geometry, data=selected_column)
gdf.crs = 'EPSG:3035'


#compute duration
gdf['duration'] = gdf.apply(lambda f:(f.geometry.length/f.speed_kmh*3.6), axis=1)

#simplify geometry
def make_segment(geom):
    c0 = geom.coords[0]
    cn = geom.coords[-1]
    return LineString([c0, cn])
gdf['geometry'] = gdf['geometry'].apply(make_segment)

print(datetime.now(), "save prepared road network")
gdf.to_file(out_folder+"test_"+str(size)+"_prepared.gpkg", driver="GPKG")
