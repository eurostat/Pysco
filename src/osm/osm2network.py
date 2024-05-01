import geopandas as gpd
from datetime import datetime
from osmutils import other_tags_to_dict

#bbox = [3700000, 2700000, 4200000, 3400000]
bbox = [4000000, 2800000, 4100000, 2900000]
osm_file = "/home/juju/geodata/OSM/europe_road_network_prep.gpkg"
out_file = "/home/juju/geodata/OSM/europe_road_network.gpkg"

print(datetime.now(), "load OSM lines")
rn = gpd.read_file(osm_file, layer='lines', driver='GPKG', bbox=bbox)
print(len(rn), "lines")

#print(datetime.now(), "filter highway != NULL")
#rn = rn[rn['highway'].notnull()]
#print(str(len(rn)), "road sections")

#print(datetime.now(), "remove columns")
#rn.drop(columns=['name', 'aerialway', 'waterway', 'barrier', 'man_made', 'z_order'], inplace=True)


def extract_attributes_from_other_tags(gdf, attributes, delete_other_tags=True):
    #initialise with None value TODO
    for attribute in attributes: gdf[attribute] = None

    #iterate through features
    for iii, feature in gdf.iterrows():
        try:
            #get other tags
            other_tags = feature.other_tags
            if other_tags == None: continue
            #transform it into a dictionnary
            other_tags_dict = other_tags_to_dict(other_tags)
            #set attribute values
            for attribute in attributes:
                if not attribute in other_tags_dict: continue
                #feature[attribute] = str(other_tags_dict[attribute])
                gdf.at[iii, attribute] = other_tags_dict[attribute]
        except Exception as e: print("", other_tags)

    #delete other_tags attribute
    if delete_other_tags: gdf.drop(columns=['other_tags'], inplace=True)


print(datetime.now(), "add attributes from other_tags")
extract_attributes_from_other_tags(rn, ['maxspeed', 'lanes', 'oneway', 'smoothness', 'surface', 'access'])


print(datetime.now(), "save")
rn.to_file(out_file, driver="GPKG")

#TODO make it a routable network
#TODO: keep only segment ?
#TODO: compute duration and keep only that ?

#Highway tag
#https://wiki.openstreetmap.org/wiki/Key:highway
#motorway, trunk, primary, secondary, tertiary, residential, service, etc.

