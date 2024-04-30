import geopandas as gpd
from datetime import datetime

#bbox = [3700000, 2700000, 4200000, 3400000]
bbox = [4000000, 2800000, 4100000, 2900000]
osm_file = "/home/juju/geodata/OSM/europe.gpkg"
out_file = "/home/juju/geodata/OSM/europe_road_networf.gpkg"


print(datetime.now(), "load OSM lines")
rn = gpd.read_file(osm_file, layer='lines', bbox=bbox)
print(str(len(rn)), "lines")

print(datetime.now(), "filter highway != NULL")
rn = rn[rn['highway'].notnull()]
print(str(len(rn)), "road sections")

print(datetime.now(), "remove columns")
rn.drop(columns=['name', 'aerialway', 'waterway', 'barrier', 'man_made', 'z_order'], inplace=True)

print(datetime.now(), "save")
rn.to_file(out_file, driver="GPKG")


#attributes:
#maxspeed
#lanes
#oneway
#smoothness
#surface
#access


#TODO: keep only segment ?
#TODO: compute duration and keep only that ?

#Highway tag
#https://wiki.openstreetmap.org/wiki/Key:highway
#motorway, trunk, primary, secondary, tertiary, residential, service, etc.

