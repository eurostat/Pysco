from accessiblity_grid_k_nearest_dijkstra import accessiblity_grid_k_nearest_dijkstra_parallel
import numpy as np

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import iter_features
from utils.tomtomutils import weight_function, is_not_snappable_fun, initial_node_level_fun, final_node_level_fun, is_start_blocked, is_end_blocked
from utils.convert import parquet_grid_to_geotiff

# folders where to find the inputs
tomtom_data_folder = "/home/juju/geodata/tomtom/"
pois_data_folder = "/home/juju/geodata/gisco/basic_services/"
# folders where to store the outputs
out_folder = '/home/juju/Bureau/test_cc/'
if not os.path.exists(out_folder): os.makedirs(out_folder)

# define output bounding box
bbox = [ 3930000, 2240000,  3960000, 2270000 ]
 

grid_resolution = 100
year = "2023"

def cell_id_fun(x,y): return "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))
def duration_simplification_fun(x): return int(round(x))

# define tomtom and POI loaders
def road_network_loader(bbox): return iter_features(tomtom_data_folder + "tomtom"+year+"12.gpkg", bbox=bbox) #, where="FOW!='20'"
def pois_loader(bbox): return iter_features(pois_data_folder+"healthcare_"+year+"_3035"+".gpkg", bbox=bbox) #, where="levels IS NULL or levels!='0'" if service=="education" else "")

# build accessibility grid
if True:
    accessiblity_grid_k_nearest_dijkstra_parallel(
        pois_loader = pois_loader,
        road_network_loader = road_network_loader,
        bbox = bbox,
        out_folder = out_folder,
        k = 3,
        weight_function = weight_function,
        is_not_snappable_fun = is_not_snappable_fun,
        initial_node_level_fun = initial_node_level_fun,
        is_start_blocked = is_start_blocked,
        is_end_blocked = is_end_blocked,
        final_node_level_fun = final_node_level_fun,
        cell_id_fun = cell_id_fun,
        grid_resolution= grid_resolution,
        cell_network_max_distance= 200,
        file_size = 30000,
        extention_buffer = 0,
        detailled = True,
        densification_distance=100,
        duration_simplification_fun = duration_simplification_fun,
        num_processors = 5,
        shuffle=True,
        show_detailled_messages = False
    )

if True:
    print("to_geotiff")
    parquet_grid_to_geotiff(
        [out_folder + "100m_3900000_2200000.parquet"],
        out_folder + "out.tiff",
        bbox = bbox,
        attributes=["duration_s_1", "duration_average_s_3"],
        parquet_nodata_values=[-1],
        dtype=np.int16,
        value_fun= lambda v:v if v<32767 else 32767, # np.int16(v),
        compress='deflate'
    )

