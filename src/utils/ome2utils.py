

def ome2_filter_road_links(gdf):
    #gdf = gdf[gdf['road_surface_category'] != 'unpaved']
    #gdf = gdf[gdf['road_surface_category'] != 'paved#unpaved']
    #gdf = gdf[gdf['road_surface_category'] != 'unpaved#paved']
    gdf = gdf[gdf['form_of_way'] != 'tractor_road']
    gdf = gdf[gdf['form_of_way'] != 'tractor_road#single_carriage_way']
    gdf = gdf[gdf['form_of_way'] != 'single_carriage_way#tractor_road']
    gdf = gdf[gdf['access_restriction'] != 'physically_impossible']
    gdf = gdf[gdf['access_restriction'] != 'private']
    gdf = gdf[gdf['access_restriction'] != 'void_restricted#private']
    gdf = gdf[gdf['access_restriction'] != 'void_restricted']
    #gdf = gdf[gdf['access_restriction'] != 'void_restricted#public_access']
    gdf = gdf[gdf['condition_of_facility'] != 'disused']
    gdf = gdf[gdf['condition_of_facility'] != 'under_construction']
    return gdf


def road_link_speed_kmh(feature):
    rsc = feature["road_surface_category"]
    fow = feature["form_of_way"]
    frc = feature["functional_road_class"]
    speed_kmh = 30
    if(rsc != 'paved'): speed_kmh = 20
    elif(fow == 'motorway'): speed_kmh = 120
    elif(fow == 'dual_carriage_way'): speed_kmh = 100
    elif(fow == 'slip_road'): speed_kmh = 80
    #elif(fow == 'single_carriage_way'): speed_kmh = 80
    elif(frc == 'main_road'): speed_kmh = 80
    elif('first_class' in frc): speed_kmh = 80
    elif('second_class' in frc): speed_kmh = 70
    elif('third_class' in frc): speed_kmh = 50
    elif('fourth_class' in frc): speed_kmh = 40
    elif('fifth_class' in frc): speed_kmh = 30
    elif('sixth_class' in frc): speed_kmh = 30
    elif(frc == 'void_unk'): speed_kmh = 30
    else: print(rsc,fow,frc)
    return speed_kmh

def ome2_duration(feature, length):
    return length/road_link_speed_kmh(feature)*3.6
