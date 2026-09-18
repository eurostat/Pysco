import sys
import os
from functools import partial
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from accessiblity_grid_k_nearest_dijkstra import accessiblity_grid_k_nearest_dijkstra_parallel
from utils.featureutils import iter_features
from utils.tomtomutils import weight_function, weight_function_length, is_not_snappable_fun, initial_node_level_fun, final_node_level_fun, is_start_blocked, is_end_blocked


def pois_loader(bbox, pois_dataset): return iter_features(pois_dataset, bbox=bbox) #, where="levels IS NULL or levels!='0'" if service=="education" else "")
def road_network_loader(bbox, tomtom_dataset): return iter_features(tomtom_dataset, bbox=bbox) #, where="FOW!='20'"
def cell_id_fun(x,y,grid_resolution): return "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))
def cost_simplification_fun(x): return int(round(x))


def compute_accessibility_grids(params, services=None, years=None, resolutions=[100]):

    if services is None: services = params["pois_datasets"].keys()

    for grid_resolution in resolutions:
        cell_id_fun_ = partial(cell_id_fun, grid_resolution=grid_resolution)

        for service in services:
            if years is None: years = params["pois_datasets"][service].keys()

            for year in years:
                print(grid_resolution, service, year)

                # define and create ouput folder, depending on year, service, resolution
                out_folder_service_year = params["out_folder"] + "out_" + service + "_" + year + "_" + str(grid_resolution) + "m/"
                os.makedirs(out_folder_service_year, exist_ok=True)

                # define tomtom loader
                tomtom_dataset = params["tomtom_datasets"][year]
                road_network_loader_ = partial(road_network_loader, tomtom_dataset=tomtom_dataset)
                #def road_network_loader(bbox): return iter_features(tomtom_dataset, bbox=bbox) #, where="FOW!='20'"

                # define POI loader
                pois_dataset = params["pois_datasets"][service][year]
                pois_loader_ = partial(pois_loader, pois_dataset=pois_dataset)
                #def pois_loader(bbox): return iter_features(pois_dataset, bbox=bbox) #, where="levels IS NULL or levels!='0'" if service=="education" else "")

                # build accessibility grid
                accessiblity_grid_k_nearest_dijkstra_parallel(
                    pois_loader = pois_loader_,
                    road_network_loader = road_network_loader_,
                    bbox = params["bbox"],
                    out_folder = out_folder_service_year,
                    k = 5 if service == "evrp" else 3,
                    weight_function = weight_function_length if service == "evrp" else weight_function,
                    is_not_snappable_fun = is_not_snappable_fun,
                    initial_node_level_fun = initial_node_level_fun,
                    is_start_blocked = is_start_blocked,
                    is_end_blocked = is_end_blocked,
                    final_node_level_fun = final_node_level_fun,
                    cell_id_fun = cell_id_fun_,
                    grid_resolution= grid_resolution,
                    cell_network_max_distance= 1500,
                    to_network_speed_ms= 1 if service == "evrp" else 15 / 3.6,
                    file_size = 200000 if grid_resolution == 100 else 500000,
                    extention_buffer = 20000 if service in ["education", "evrp"] else 60000,
                    detailled = True,
                    densification_distance = grid_resolution,
                    cost_simplification_fun = cost_simplification_fun,
                    threshold_connected_component_to_remove_node_nb = 50,
                    num_processors = 3 if service == "evrp" else 3 if service == "education" else 2,
                    shuffle=True,
                    show_detailled_messages = False
                )

