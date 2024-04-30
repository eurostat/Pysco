

#function to convert 'other_tags' attribute into a dictionnary
def other_tags_to_dict(input_text):
    pairs = input_text.split('","')
    result_dict = {}
    for pair in pairs:
        key, value = pair.split('"=>"')
        result_dict[key.strip()] = value.strip().replace('"','')
    return result_dict
