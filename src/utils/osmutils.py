

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
    speed_kmh = 30

    hw = feature.hw
    if hw == 'motoway': speed_kmh = 100
    elif hw == 'trunk': speed_kmh = 70
    elif hw == 'primary': speed_kmh = 70
    elif hw == 'secondary': speed_kmh = 60
    elif hw == 'tertiary': speed_kmh = 40
    elif hw == 'residential': speed_kmh = 30
    elif hw == 'unclassified': speed_kmh = 30
    elif hw == '': speed_kmh = 30

    #get other tags
    other_tags = feature.other_tags
    if other_tags == None: return speed_kmh

    #TODO
    return speed_kmh

def osm_duration(feature, length):
    return length/osm_road_link_speed_kmh(feature)*3.6
