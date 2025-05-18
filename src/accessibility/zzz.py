import geopandas as gpd
from accessiblity_grid_k_nearest_dijkstra import accessiblity_grid_k_nearest_dijkstra

 
#luxembourg
bbox = [4030000, 2940000, 4050000, 2960000]
#marseille
#bbox = [3900000, 2200000, 4000000, 2300000]
#big
#bbox = [3500000, 2000000, 4000000, 2500000]

#test
#bbox = [3800000, 2300000, 4000000, 2500000]

grid_resolution = 100


def direction_fun(feature):
    d = feature.ONEWAY
    if d==None or d=="": return 'both'
    if d=="FT": return 'forward'
    if d=="TF": return 'backward'
    print("Unexpected driving direction: ", d)
    return None


accessiblity_grid_k_nearest_dijkstra(
    pois_loader = lambda bbox: gpd.read_file('/home/juju/geodata/gisco/basic_services/education_2023_3035.gpkg', bbox=bbox),
    road_network_loader = lambda bbox: gpd.read_file('/home/juju/geodata/tomtom/tomtom_202312.gpkg', bbox=bbox).query("ONEWAY != 'N'"),
    bbox = bbox,
    out_folder = "/home/juju/Bureau/",
    out_file = "grid_education",
    k = 3,
    weight_function = lambda feature, length : -1 if feature.KPH==0 else 1.1*length/feature.KPH*3.6,
    #direction_fun = direction_fun,
    cell_id_fun = lambda x,y: "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x)),
    grid_resolution= grid_resolution,
    cell_network_max_distance= grid_resolution * 1.5,
    partition_size = 20000,
    extention_buffer = 10000,
    detailled = True,
    crs = 'EPSG:3035',
    num_processors_to_use = 8,
    save_GPKG = True,
    save_CSV = False,
    save_parquet = False
)

