
from accessiblity_grid_k_nearest_dijkstra import accessiblity_grid_k_nearest_dijkstra_parallel

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import iter_features
from utils.tomtomutils import weight_function, direction_fun, is_not_snappable_fun, initial_node_level_fun, final_node_level_fun

# TODO
# correct speed !


# folders where to find the inputs
tomtom_data_folder = "/home/juju/geodata/tomtom/"
pois_data_folder = "/home/juju/geodata/gisco/charging_stations/"
# folders where to store the outputs
out_folder = '/home/juju/gisco/accessibility_charging_stations/'


# define output bounding box
# whole europe
bbox = [ 900000, 900000, 6600000, 5500000 ]


for grid_resolution in [100]: # 1000

    for year in ["2025", "2023"]:

        # detailled network decomposition only when resolution to 100m
        detailled_network_decomposition = True
        # densification
        densification_distance = grid_resolution
        # keep cells whose centre is within 3 * grid_resolution from a network node
        cell_network_max_distance = 3 * grid_resolution
        # tile file size, in m
        file_size = 200000

        def cell_id_fun(x,y): return "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))
        def duration_simplification_fun(x): return int(round(x))

        # choose number of processors, depending on service type and resolution
        num_processors_to_use = 2

        # define tile buffer, depending on service type
        extention_buffer = 20000

        # define and create ouput folder, depending on year, service, resolution
        out_folder_service_year = out_folder + "out_" + year + "_" + str(grid_resolution) + "m/"
        if not os.path.exists(out_folder_service_year): os.makedirs(out_folder_service_year)

        # define tomtom year TODO: use other version, closer from POI reference year
        tomtom_year = "2023"


        # define tomtom and POI loaders
        def road_network_loader(bbox): return iter_features(tomtom_data_folder + "tomtom_"+tomtom_year+"12.gpkg", bbox=bbox)
        def pois_loader(bbox): return iter_features(pois_data_folder+year+".gpkg", bbox=bbox)

        # build accessibility grid
        accessiblity_grid_k_nearest_dijkstra_parallel(
            pois_loader = pois_loader,
            road_network_loader = road_network_loader,
            bbox = bbox,
            out_folder = out_folder_service_year,
            k = 5,
            weight_function = weight_function,
            direction_fun = direction_fun,
            is_not_snappable_fun = is_not_snappable_fun,
            initial_node_level_fun = initial_node_level_fun,
            final_node_level_fun = final_node_level_fun,
            cell_id_fun = cell_id_fun,
            grid_resolution= grid_resolution,
            cell_network_max_distance= grid_resolution * 2,
            file_size = file_size,
            extention_buffer = extention_buffer,
            detailled = detailled_network_decomposition,
            densification_distance=densification_distance,
            duration_simplification_fun = duration_simplification_fun,
            num_processors = num_processors_to_use,
            shuffle=True
        )

