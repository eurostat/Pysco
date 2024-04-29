import geopandas as gpd
from geopandas.tools import overlay
from datetime import datetime
from lib.geomutils import decompose_point_array

folder = '/home/juju/gisco/OME2_analysis/'
file_path = '/home/juju/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg'

print(datetime.now(), "load paths")
paths = gpd.read_file(folder+"ome2_validation_paths_be_fr.gpkg")
print(str(len(paths)), "paths")

print(datetime.now(), "load boundaries")
borders = gpd.read_file(folder+"bnd.gpkg")
print(str(len(borders)), "boundaries")

print(datetime.now(), "compute intersections")
intersection = overlay(borders, paths, how='intersection', keep_geom_type=False)
print(str(len(intersection)), "intersections")
del paths, borders

#keep only geometries
intersection = intersection.geometry.values

print(datetime.now(), "decompose multipoints")
intersection = decompose_point_array(intersection)
print(str(len(intersection)), "intersections")

print(datetime.now(), "remove duplicates")
intersection = list(set(intersection))
print(str(len(intersection)), "intersections")

print(datetime.now(), "save intersections")
gpd.GeoDataFrame(geometry=intersection).to_file(folder+"intersections.gpkg", driver="GPKG")
