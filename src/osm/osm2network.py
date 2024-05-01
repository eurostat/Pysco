import geopandas as gpd
from datetime import datetime
from osmutils import extract_attributes_from_other_tags

#bbox = [3700000, 2700000, 4200000, 3400000]
bbox = [4000000, 2800000, 4100000, 2900000]
osm_file = "/home/juju/geodata/OSM/europe_road_network_prep.gpkg"
out_file = "/home/juju/geodata/OSM/europe_road_network.gpkg"

print(datetime.now(), "load OSM lines")
rn = gpd.read_file(osm_file, layer='lines', driver='GPKG', bbox=bbox)
print(len(rn), "lines")

print(datetime.now(), "extract attributes from other_tags")
extract_attributes_from_other_tags(rn, ['maxspeed', 'lanes', 'oneway', 'smoothness', 'surface', 'access'])

print(datetime.now(), "save")
rn.to_file(out_file, driver="GPKG")

#TODO make it a routable network
#TODO: keep only segment ?
#TODO: compute duration and keep only that ?

#Highway tag
#https://wiki.openstreetmap.org/wiki/Key:highway
#motorway, trunk, primary, secondary, tertiary, residential, service, etc.

