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


accessiblity_grid_k_nearest_dijkstra(
    pois_loader = lambda bbox: gpd.read_file('/home/juju/geodata/gisco/basic_services/healthcare_2023_3035.gpkg', bbox=bbox),
    road_network_loader = lambda bbox: gpd.read_file('/home/juju/geodata/tomtom/tomtom_202312.gpkg', bbox=bbox),
    bbox = bbox,
    out_folder = "/home/juju/Bureau/",
    out_file = "grid",
    k = 3,
    weight_function = lambda feature, length : -1 if feature.KPH==0 else 1.1*length/feature.KPH*3.6,
    direction_fun=lambda feature:"both",
    cell_id_fun = lambda x,y: "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x)),
    grid_resolution= grid_resolution,
    cell_network_max_distance= grid_resolution * 1.5,
    partition_size = 10000,
    extention_buffer = 10000,
    #detailled = False, #TODO
    crs = 'EPSG:3035',
    num_processors_to_use = 4,
    save_GPKG = True,
    save_CSV = False,
    save_parquet = False
)

