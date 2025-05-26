from math import floor
from accessiblity_grid_k_nearest_dijkstra import accessiblity_grid_k_nearest_dijkstra

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import iter_features
from utils.convert import parquet_grid_to_gpkg


#TODO: 1000*1000 instead of 500*500 ?
#TODO take private access sections - tracks
#TODO check ferries
#TODO check paris centre bug - pedestrian areas
#TODO school: exclude some...
#TODO school, by walking
#TODO ajouter code pays/nuts aux cellules - do it in external function
#TODO remove DE, RS, CH, etc.
#TODO handle case when speed depends on driving direction

#TODO no longer do 500km tiles ?
#TODO QGIS plugin for parquet grids


#set bbox for test area
#luxembourg
bbox = [4030000, 2930000, 4060000, 2960000]
#big
#bbox = [3500000, 2000000, 4000000, 2500000]
#test
#bbox = [3800000, 2300000, 3900000, 2400000]
#whole europe
#bbox = [ 1000000, 500000, 6000000, 5500000 ]


grid_resolution = 100
year = "2023"
service = "education"


# driving direction
def direction_fun(feature):
    d = feature['properties']['ONEWAY']
    if d==None or d=="": return 'both'
    if d=="FT": return 'forward'
    if d=="TF": return 'backward'
    print("Unexpected driving direction: ", d)
    return None

def road_network_loader(bbox): return iter_features("/home/juju/geodata/tomtom/tomtom_"+year+"12.gpkg", bbox=bbox, where="ONEWAY ISNULL or ONEWAY != 'N'")
def pois_loader(bbox): return iter_features("/home/juju/geodata/gisco/basic_services/"+service+"_"+year+"_3035.gpkg", bbox=bbox)
def weight_function(feature, length): return -1 if feature['properties']['KPH']==0 else 1.1*length/feature['properties']['KPH']*3.6
def cell_id_fun(x,y): return "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))
def is_not_snappable_fun(f): return f['properties']['FOW'] in [1,10,12,6] or f['properties']['FREEWAY'] == 1
def initial_node_level_fun(f): return f['properties']['F_ELEV']
def final_node_level_fun(f): return f['properties']['T_ELEV']
def duration_simplification_fun(x): return round(x,1)

# build accessibility grid
accessiblity_grid_k_nearest_dijkstra(
    pois_loader = pois_loader,
    road_network_loader = road_network_loader,
    bbox = bbox,
    out_parquet_file = "/home/juju/gisco/accessibility/grid.parquet",
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
    extention_buffer = 0,
    detailled = True,
    duration_simplification_fun = duration_simplification_fun,
    num_processors_to_use = 1,
)

print("Convert parquet to GPKG")
parquet_grid_to_gpkg(
    '/home/juju/gisco/accessibility/grid.parquet',
    '/home/juju/gisco/accessibility/grid.gpkg',
)

