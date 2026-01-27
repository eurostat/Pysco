from accessiblity_grid_k_nearest_dijkstra import accessiblity_grid_k_nearest_dijkstra_parallel

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import iter_features
from utils.tomtomutils import weight_function, is_not_snappable_fun, initial_node_level_fun, final_node_level_fun, is_start_blocked, is_end_blocked

#TODO
# connex component issue:
# detect connex components
# either remove the CCs, OR reconnect them, OR ensure it is not deconnected
# secondary services accessibility
# accessibility walking, cycling ?


# folders where to find the inputs
tomtom_data_folder = "/home/juju/geodata/tomtom/"
pois_data_folder = "/home/juju/geodata/gisco/basic_services/"
# folders where to store the outputs
out_folder = '/home/juju/gisco/accessibility/'

# define output bounding box
# whole europe
bbox = [ 900000, 900000, 6600000, 5500000 ]
#luxembourg
#bbox = [4030000, 2930000, 4060000, 2960000]
#greece
#bbox = [ 5000000, 1500000, 5500000, 2000000 ]


for grid_resolution in [100]: # 1000

    for service in ["healthcare", "education"]:
        for year in ["2023", "2020"]: #"2023"

            def cell_id_fun(x,y): return "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))
            def duration_simplification_fun(x): return int(round(x))

            # choose number of processors, depending on service type and resolution
            if grid_resolution == 100:
                num_processors_to_use = 6 if service == "education" else 2 #2
            else: num_processors_to_use = 10

            # define and create ouput folder, depending on year, service, resolution
            out_folder_service_year = out_folder + "out_" + service + "_" + year + "_" + str(grid_resolution) + "m/"
            os.makedirs(out_folder_service_year, exist_ok=True)

            # define tomtom year
            tomtom_year = "2019" if year == "2020" else year

            # define tomtom and POI loaders
            def road_network_loader(bbox): return iter_features(tomtom_data_folder + "tomtom"+tomtom_year+"12.gpkg", bbox=bbox) #, where="FOW!='20'"
            def pois_loader(bbox): return iter_features(pois_data_folder+service+"_"+year+"_3035"+".gpkg", bbox=bbox) #, where="levels IS NULL or levels!='0'" if service=="education" else "")

            # build accessibility grid
            accessiblity_grid_k_nearest_dijkstra_parallel(
                pois_loader = pois_loader,
                road_network_loader = road_network_loader,
                bbox = bbox,
                out_folder = out_folder_service_year,
                k = 3,
                weight_function = weight_function,
                is_not_snappable_fun = is_not_snappable_fun,
                initial_node_level_fun = initial_node_level_fun,
                is_start_blocked = is_start_blocked,
                is_end_blocked = is_end_blocked,
                final_node_level_fun = final_node_level_fun,
                cell_id_fun = cell_id_fun,
                grid_resolution= grid_resolution,
                cell_network_max_distance= 1500,
                to_network_speed_ms= 15 /3.6, # 15km/h by car
                file_size = 200000 if grid_resolution == 100 else 500000,
                extention_buffer = 20000 if service=="education" else 60000,
                detailled = True,
                densification_distance = grid_resolution,
                duration_simplification_fun = duration_simplification_fun,
                num_processors = num_processors_to_use,
                shuffle=True,
                show_detailled_messages = False
            )

