from accessiblity_grid_k_nearest_dijkstra import accessiblity_grid_k_nearest_dijkstra_parallel

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import iter_features
from utils.tomtomutils import weight_function, is_not_snappable_fun, initial_node_level_fun, final_node_level_fun

#TODO
# weight function: merge both
# handle case when speed_pos and speed_neg non defined
# education: remove non-primary for those with with type differenciation


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

    for year in ["2020", "2023"]: #"2023"

        for service in ["healthcare"]:
            file_path_suffix = "_20251020"

            # detailled network decomposition only when resolution to 100m
            detailled_network_decomposition = grid_resolution == 100
            # densification
            densification_distance = grid_resolution
            # keep cells whose centre is within 3 * grid_resolution from a network node
            cell_network_max_distance = 3 * grid_resolution
            # tile file size, in m
            file_size = 200000 if grid_resolution == 100 else 500000

            def cell_id_fun(x,y): return "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))
            def duration_simplification_fun(x): return int(round(x))

            # choose number of processors, depending on service type and resolution
            if grid_resolution == 100:
                num_processors_to_use = 6 if service == "education" else 4 #3
            else: num_processors_to_use = 10

            # define tile buffer, depending on service type
            extention_buffer = 20000 if service=="education" else 60000

            # define and create ouput folder, depending on year, service, resolution
            out_folder_service_year = out_folder + "out_" + service + "_" + year + "_" + str(grid_resolution) + "m/"
            if not os.path.exists(out_folder_service_year): os.makedirs(out_folder_service_year)

            # define tomtom year TODO: use other version, closer from POI reference year
            tomtom_year = "2019" if year == "2020" else year

            # define tomtom and POI loaders
            def road_network_loader(bbox): return iter_features(tomtom_data_folder + "tomtom"+tomtom_year+"12.gpkg", bbox=bbox)
            def pois_loader(bbox): return iter_features(pois_data_folder+service+"_"+year+"_3035"+file_path_suffix+".gpkg", bbox=bbox, where="levels IS NULL or levels!='0'" if service=="education" else "")

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
                shuffle=True,
                #show_detailled_messages = True
            )

