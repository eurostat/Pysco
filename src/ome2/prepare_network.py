import geopandas as gpd
from shapely.geometry import LineString
from datetime import datetime

out_folder = '/home/juju/Bureau/gisco/OME2_analysis/'

print(datetime.now(), "loading")
size = 60000
gdf = gpd.read_file(out_folder+"test_"+str(size)+".gpkg")
print(str(len(gdf)) + " links")
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
print(str(len(gdf)) + " links")
#print(gdf.dtypes)

#define speed
def speed_function(f):
    rsc = f["road_surface_category"]
    fow = f["form_of_way"]
    frc = f["functional_road_class"]
    speed_kmh = 30
    if(rsc != 'paved'): speed_kmh = 20
    elif(fow == 'motorway'): speed_kmh = 120
    elif(fow == 'dual_carriage_way'): speed_kmh = 100
    elif(fow == 'slip_road'): speed_kmh = 80
    #elif(fow == 'single_carriage_way'): speed_kmh = 80
    elif(frc == 'main_road'): speed_kmh = 80
    elif(frc == 'first_class'): speed_kmh = 80
    elif(frc == 'second_class'): speed_kmh = 70
    elif(frc == 'third_class'): speed_kmh = 50
    elif(frc == 'fourth_class'): speed_kmh = 40
    elif(frc == 'fifth_class'): speed_kmh = 30
    elif(frc == 'void_unk'): speed_kmh = 30
    else: print(rsc,fow,frc)
    return speed_kmh

#compute speed
gdf['speed_kmh'] = gdf.apply(speed_function, axis=1)

#keep only speed column
geometry = gdf.geometry
selected_column = gdf['speed_kmh']
gdf = gpd.GeoDataFrame(geometry=geometry, data=selected_column)
gdf.crs = 'EPSG:3035'


#compute duration
gdf['duration'] = gdf.apply(lambda f:(f.geometry.length/f.speed_kmh*3.6), axis=1)

#simplify geometry
def make_segment(geom):
    c0 = geom.coords[0]
    cn = geom.coords[-1]
    return LineString([c0, cn])
gdf['geometry'] = gdf['geometry'].apply(make_segment)

print(datetime.now(), "save prepared road network")
gdf.to_file(out_folder+"test_"+str(size)+"_prepared.gpkg", driver="GPKG")
