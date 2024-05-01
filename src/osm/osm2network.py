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


#TODO extract to osmutils
def extract_attributes_from_other_tags(gdf, attributes, delete_other_tags=True):

    #initialise attributes with None value
    for attribute in attributes:
        gdf[attribute] = None

    #iterate through features
    for i, feature in gdf.iterrows():
        try:
            #get other tags
            other_tags = feature.other_tags
            if other_tags == None: continue
            #transform it into a dictionnary
            other_tags_dict = other_tags_to_dict(other_tags)
            #set attribute values
            for attribute in attributes:
                if attribute in other_tags_dict: gdf.at[i, attribute] = other_tags_dict[attribute]
        except Exception as e: print("Could not parse other_tags attribute: ", other_tags)

    #delete other_tags attribute
    if delete_other_tags: gdf.drop(columns=['other_tags'], inplace=True)


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

