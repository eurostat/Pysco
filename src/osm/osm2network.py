import geopandas as gpd
from datetime import datetime
from utils.osmutils import extract_attributes_from_other_tags

bbox = [3700000, 2700000, 4200000, 3400000]
#bbox = [4000000, 2800000, 4100000, 2900000]
osm_file = "/home/juju/geodata/OSM/europe_road_network_prep.gpkg"
out_file = "/home/juju/geodata/OSM/europe_road_network.gpkg"

print(datetime.now(), "load OSM prepared network")
rn = gpd.read_file(osm_file, bbox=bbox)
print(len(rn), "lines")

print(datetime.now(), "extract attributes from other_tags")
extract_attributes_from_other_tags(rn, ['maxspeed', 'lanes', 'oneway', 'smoothness', 'surface', 'access'])

print(datetime.now(), "save")
rn.to_file(out_file, driver="GPKG")

