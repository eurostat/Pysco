from accessiblity_grid_k_nearest_dijkstra import accessiblity_grid_k_nearest_dijkstra_parallel

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import iter_features
from utils.tomtomutils import weight_function, weight_function_length, is_not_snappable_fun, initial_node_level_fun, final_node_level_fun, is_start_blocked, is_end_blocked
from accessibility.utils import pois_datasets, tomtom_datasets, bbox, out_folder

# TODO
# accessibility to schools by walking
# secondary education services accessibility


for grid_resolution in [100]: # 1000

    for service in ["evrp"]: #["healthcare", "education", "evrp"]:
        years = pois_datasets[service].keys()

        for year in years:
            print(grid_resolution, service, year)

            def cell_id_fun(x,y): return "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))
            def cost_simplification_fun(x): return int(round(x))

            # define and create ouput folder, depending on year, service, resolution
            out_folder_service_year = out_folder + "out_" + service + "_" + year + "_" + str(grid_resolution) + "m/"
            os.makedirs(out_folder_service_year, exist_ok=True)

            # define tomtom loader
            tomtom_dataset = tomtom_datasets[year]
            def road_network_loader(bbox): return iter_features(tomtom_dataset, bbox=bbox) #, where="FOW!='20'"

            # define POI loader
            pois_dataset = pois_datasets[service][year]
            def pois_loader(bbox): return iter_features(pois_dataset, bbox=bbox) #, where="levels IS NULL or levels!='0'" if service=="education" else "")

            # build accessibility grid
            accessiblity_grid_k_nearest_dijkstra_parallel(
                pois_loader = pois_loader,
                road_network_loader = road_network_loader,
                bbox = bbox,
                out_folder = out_folder_service_year,
                k = 5 if service == "evrp" else 3,
                weight_function = weight_function_length if service == "evrp" else weight_function,
                is_not_snappable_fun = is_not_snappable_fun,
                initial_node_level_fun = initial_node_level_fun,
                is_start_blocked = is_start_blocked,
                is_end_blocked = is_end_blocked,
                final_node_level_fun = final_node_level_fun,
                cell_id_fun = cell_id_fun,
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

