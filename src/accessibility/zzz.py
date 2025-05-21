import geopandas as gpd
from accessiblity_grid_k_nearest_dijkstra import accessiblity_grid_k_nearest_dijkstra
import fiona
from fiona.env import Env
from shapely.geometry import shape, box

def iter_features(filepath, layername=None, bbox=None, where=None):
    """
    :param bbox: Tuple (minx, miny, maxx, maxy) pour filtrer géographiquement
    :param where: Clause SQL WHERE (ex : "population > 1000")
    :return: Itérateur sur les features filtrées
    """
    with fiona.open(filepath, layer=layername) as src:
        for fid, feature in src.items(bbox=bbox, where=where):
            yield feature

    '''
    with Env():
        with fiona.open(filepath, layer=layername) as src:
            bbox_geom = box(*bbox) if bbox else None

            for feature in src:
                geom = shape(feature['geometry'])
                if bbox_geom and not geom.intersects(bbox_geom): continue
                if where:
                    try:
                        if not eval(where, {}, feature['properties']): continue
                    except Exception as e:
                        print(f"Erreur dans la clause WHERE : {e}")
                        continue
                yield feature
'''

#for feat in iter_features("data.gpkg", "villes", bbox=(2.0, 48.0, 3.0, 49.0), where="population > 1000"):
#    print(feat['properties']['nom'], feat['properties']['population'])


#luxembourg
bbox = [4030000, 2930000, 4060000, 2960000]
bbox_ = (4030000, 2930000, 4060000, 2970000)
#big
#bbox = [3500000, 2000000, 4000000, 2500000]

#test
#bbox = [3800000, 2300000, 3900000, 2400000]

grid_resolution = 100


#TODO improve data loading: use fiona iterator through necessary features, with the where - no loading necesary?
#TODO handle case when speed depends on driving direction


def direction_fun(feature):
    d = feature.ONEWAY
    if d==None or d=="": return 'both'
    if d=="FT": return 'forward'
    if d=="TF": return 'backward'
    print("Unexpected driving direction: ", d)
    return None

#def road_network_loader(bbox): return gpd.read_file('/home/juju/geodata/tomtom/tomtom_202312.gpkg', bbox=bbox).query("ONEWAY != 'N'")
def road_network_loader(bbox): return iter_features("/home/juju/geodata/tomtom/tomtom_202312.gpkg", bbox=bbox_)
#gpd.read_file('/home/juju/geodata/tomtom/tomtom_202312.gpkg', bbox=bbox).query("ONEWAY != 'N'")
def pois_loader(bbox): return gpd.read_file('/home/juju/geodata/gisco/basic_services/healthcare_2023_3035.gpkg', bbox=bbox)
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
    partition_size = 30000,
    extention_buffer = 10000,
    detailled = True,
    duration_simplification_fun = duration_simplification_fun,
    crs = 'EPSG:3035',
    num_processors_to_use = 1,
    save_GPKG = True,
    save_CSV = False,
    save_parquet = False
)


