import geopandas as gpd
from datetime import datetime

#bbox = [3700000, 2700000, 4200000, 3400000]
bbox = [4000000, 2800000, 4100000, 2900000]
osm_file = "/home/juju/geodata/OSM/europe.gpkg"
out_file = "/home/juju/geodata/OSM/europe_road_network.gpkg"


print(datetime.now(), "load OSM lines")
rn = gpd.read_file(osm_file, layer='lines', bbox=bbox)
print(str(len(rn)), "lines")

print(datetime.now(), "filter highway != NULL")
rn = rn[rn['highway'].notnull()]
print(str(len(rn)), "road sections")

print(datetime.now(), "remove columns")
rn.drop(columns=['name', 'aerialway', 'waterway', 'barrier', 'man_made', 'z_order'], inplace=True)

#function to convert 'other_tags' attribute into a dictionnary
def string_to_dict(input_string):
    pairs = input_string.replace('"', '').split(',')
    result_dict = {}
    for pair in pairs:
        key, value = pair.split('=>')
        result_dict[key.strip()] = value.strip()
    return result_dict

print(datetime.now(), "add attributes from other_tags")

#add new attributes, set to None
attributes = ['maxspeed', 'lanes', 'oneway', 'smoothness', 'surface', 'access']
for attribute in attributes: rn[attribute] = None

for iii, r in rn.iterrows():
    #get other tags
    ot = r.other_tags
    if ot == None: continue
    try:
        #transform it into a dictionnary
        otd = string_to_dict(ot)
        #set attribute values
        for attribute in attributes: r[attribute] = otd[attribute] if attribute in otd else None
    except Exception as e: print(ot)

print(datetime.now(), "remove other_tags")
rn.drop(columns=['other_tags'], inplace=True)

print(datetime.now(), "save")
rn.to_file(out_file, driver="GPKG")



#TODO make it a routable network
#TODO: keep only segment ?
#TODO: compute duration and keep only that ?

#Highway tag
#https://wiki.openstreetmap.org/wiki/Key:highway
#motorway, trunk, primary, secondary, tertiary, residential, service, etc.

