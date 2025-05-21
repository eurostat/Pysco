import geopandas as gpd
from accessiblity_grid_k_nearest_dijkstra import accessiblity_grid_k_nearest_dijkstra


#luxembourg
bbox = [4030000, 2940000, 4050000, 2960000]
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


#TODO fix parallelism
#TODO improve data loading: use fiona to load only necessary features, with the where ?
#TODO handle case when speed depends on driving direction

def pois_loader(bbox): return gpd.read_file('/home/juju/geodata/gisco/basic_services/healthcare_2023_3035.gpkg', bbox=bbox)
def road_network_loader(bbox): return lambda bbox: gpd.read_file('/home/juju/geodata/tomtom/tomtom_202312.gpkg', bbox=bbox).query("ONEWAY != 'N'")
def weight_function(feature, length): return -1 if feature.KPH==0 else 1.1*length/feature.KPH*3.6
def cell_id_fun(x,y): return "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))
def is_not_snappable_fun(f): return f.RAMP==1 or f.FOW==5 or (f.FOW==1 and f.FRC==0)
def initial_node_level_fun(f): return f.F_ELEV
def final_node_level_fun(f): return f.T_ELEV
def duration_simplification_fun(x): return round(x,1)


accessiblity_grid_k_nearest_dijkstra(
    pois_loader = pois_loader,
    road_network_loader = road_network_loader,
    bbox = bbox,
    out_folder = "/home/juju/Bureau/",
    out_file = "grid",
    k = 3,
    weight_function = weight_function,
    direction_fun = direction_fun,
    is_not_snappable_fun = is_not_snappable_fun,
    initial_node_level_fun = initial_node_level_fun,
    final_node_level_fun = final_node_level_fun,
    cell_id_fun = cell_id_fun,
    grid_resolution= grid_resolution,
    cell_network_max_distance= grid_resolution * 1.5,
    partition_size = 5000,
    extention_buffer = 2000,
    detailled = True,
    duration_simplification_fun = duration_simplification_fun,
    crs = 'EPSG:3035',
    num_processors_to_use = 10,
    save_GPKG = True,
    save_CSV = False,
    save_parquet = False
)


