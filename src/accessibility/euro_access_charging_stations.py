
from math import floor
from accessiblity_grid_k_nearest_dijkstra import accessiblity_grid_k_nearest_dijkstra_parallel

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import iter_features
from utils.tomtomutils import weight_function, direction_fun, is_not_snappable_fun, initial_node_level_fun, final_node_level_fun




# folders where to find the inputs
tomtom_data_folder = "/home/juju/geodata/tomtom/"
pois_data_folder = "/home/juju/geodata/gisco/charging_stations/"
# folders where to store the outputs
out_folder = '/home/juju/gisco/accessibility_charging_stations/'

# TODO



