

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

def ome2_duration(f):
    return 1
