import geopandas as gpd
from geopandas.tools import overlay
from datetime import datetime
from geomutils import decompose_multipoints

folder = '/home/juju/Bureau/gisco/OME2_analysis/'
file_path = '/home/juju/Bureau/gisco/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg'

print(datetime.now(), "load paths")
paths = gpd.read_file(folder+"ome2_validation_paths_be_fr.gpkg")
print(str(len(paths)), "paths")

print(datetime.now(), "load boundaries")
borders = gpd.read_file(folder+"bnd.gpkg")
print(str(len(borders)), "boundaries")

print(datetime.now(), "compute intersections")
intersection = overlay(borders, paths, how='intersection', keep_geom_type=False)
print(str(len(intersection)), "intersections")

#keep only geometry
intersection = intersection[['geometry']]

print(datetime.now(), "decompose multipoints")
intersection['geometry'] = intersection.apply(decompose_multipoints, axis=1)

print(datetime.now(), "remove duplicates")
intersection = intersection.drop_duplicates(subset='geometry')
intersection.reset_index(drop=True, inplace=True)
print(str(len(intersection)), "intersections")

print(datetime.now(), "save intersections")
intersection.to_file(folder+"intersections.gpkg", driver="GPKG")
