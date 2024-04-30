import geopandas as gpd
from datetime import datetime



osm_file = "/home/juju/geodata/OSM/europe.gpkg"


print(datetime.now(), "load OSM lines")
rn = gpd.read_file(osm_file, layer='lines')
print(str(len(rn)), "lines")

print(datetime.now(), "filter highway != NULL")
rn = rn[rn['highway'].notnull()]
print(str(len(rn)), "road sections")

print(datetime.now(), "remove columns")
rn.drop(columns=['name', 'aerialway', 'waterway', 'barrier', 'man_made', 'z_order'], inplace=True)


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

