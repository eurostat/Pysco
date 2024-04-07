import geopandas as gpd
from shapely.geometry import LineString,MultiPoint,Point
from datetime import datetime
from geomutils import decompose_line

folder = '/home/juju/Bureau/gisco/OME2_analysis/'
file_path = '/home/juju/Bureau/gisco/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg'

print(datetime.now(), "load nodes")
points_gdf = gpd.read_file(folder+"xborder_nodes.gpkg")
print(str(len(points_gdf)) + " nodes")

print(datetime.now(), "load countries")
polygons_gdf = gpd.read_file(file_path, layer='au_administrative_unit_area_1')
print(str(len(polygons_gdf)) + " countries")

print(datetime.now(), "do spatial join")
points_with_country = gpd.sjoin(points_gdf, polygons_gdf[['country', 'geometry']], how='left', predicate='within')
points_with_country = points_with_country.drop(columns=['index_right']).rename(columns={'country': 'country_id'})
print(str(len(points_with_country)) + " nodes")

print(datetime.now(), "save")
points_with_country.to_file(folder+"xborder_nodes_stamped.gpkg", driver="GPKG")
