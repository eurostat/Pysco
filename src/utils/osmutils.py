

#function to convert 'other_tags' attribute into a dictionnary
def other_tags_to_dict(input_text):
    pairs = input_text.split('","')
    result_dict = {}
    for pair in pairs:
        key, value = pair.split('"=>"')
        result_dict[key.strip()] = value.strip().replace('"','')
    return result_dict


#extract attributes from other_tags for a geodataframe
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



def osm_road_link_speed_kmh(feature):
    #default value
    speed_kmh = 30

    hw = feature.highway
    if hw == 'motoway': speed_kmh = 110
    elif hw == 'trunk': speed_kmh = 80
    elif hw == 'primary': speed_kmh = 80
    elif hw == 'secondary': speed_kmh = 70
    elif hw == 'tertiary': speed_kmh = 50
    elif hw == 'residential': speed_kmh = 30
    elif hw == 'unclassified': speed_kmh = 30

    if hw == 'motoway_link': speed_kmh = 80
    elif hw == 'trunk_link': speed_kmh = 60
    elif hw == 'primary_link': speed_kmh = 60
    elif hw == 'secondary_link': speed_kmh = 50
    elif hw == 'tertiary_link': speed_kmh = 40

    elif hw == 'living_street': speed_kmh = 30
    elif hw == 'service': speed_kmh = 30
    elif hw == 'pedestrian': speed_kmh = 5
    elif hw == 'track': speed_kmh = 10
    elif hw == 'footway': speed_kmh = 5
    elif hw == 'bridleway': speed_kmh = 5
    elif hw == 'steps': speed_kmh = 5
    elif hw == 'corridor': speed_kmh = 5
    elif hw == 'path': speed_kmh = 5
    elif hw == 'via_ferrata': speed_kmh = 5

    elif hw == 'cycleway': speed_kmh = 10

    elif hw == 'construction': speed_kmh = 10
    elif hw == 'proposed': speed_kmh = 10

    #get other tags
    #other_tags = feature.other_tags
    #if other_tags == None: return speed_kmh

    return speed_kmh

def osm_duration(feature, length):
    return length/osm_road_link_speed_kmh(feature)*3.6
