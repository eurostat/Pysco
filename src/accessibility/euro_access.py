from math import floor
from accessiblity_grid_k_nearest_dijkstra import accessiblity_grid_k_nearest_dijkstra_parallel

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import iter_features
from utils.tomtomutils import weight_function, direction_fun, is_not_snappable_fun, initial_node_level_fun, final_node_level_fun



#TODO add missing countries (DE) from internal data
#TODO healthcare: new 2023 with new EL
#TODO check discontinuities ! SE, etc.
#check: FEATTYP=4110 FRC 0 to 6

#TODO QGIS plugin for parquet grids ?
#TODO handle case when speed depends on driving direction ?



# where to store the outputs
out_folder = '/home/juju/gisco/accessibility/'

# define output bounding box
# whole europe
bbox = [ 900000, 900000, 6600000, 5500000 ]
#luxembourg
#bbox = [4030000, 2930000, 4060000, 2960000]
#greece
#bbox = [ 5000000, 1500000, 5500000, 2000000 ]


for year in ["2023","2020"]:

    for service in ["education", "healthcare"]:

        for grid_resolution in [100]:

            # detailled network decomposition only when resolution to 100m
            detailled_network_decomposition = grid_resolution == 100
            # densification
            densification_distance = grid_resolution
            cell_network_max_distance = grid_resolution * 3
            file_size = 200000 if grid_resolution == 100 else 500000

            def cell_id_fun(x,y): return "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))
            def duration_simplification_fun(x): return int(round(x))

            # clamp bbox to fit with file_size
            clamp = lambda v : floor(v/file_size)*file_size
            [xmin,ymin,xmax,ymax] = [clamp(v) for v in bbox]
            bbox = [xmin,ymin,xmax,ymax]

            if grid_resolution == 100:
                num_processors_to_use = 6 if service == "education" else 4 #3
            else: num_processors_to_use = 10
            extention_buffer = 20000 if service=="education" else 60000

            # ouput folder
            out_folder_service_year = out_folder + "out_" + service + "_" + year + "_" + str(grid_resolution) + "m/"
            if not os.path.exists(out_folder_service_year): os.makedirs(out_folder_service_year)

            tomtom_year = "2019" if year == "2020" else year
            def road_network_loader(bbox): return iter_features("/home/juju/geodata/tomtom/tomtom_"+tomtom_year+"12.gpkg", bbox=bbox)
            def pois_loader(bbox): return iter_features("/home/juju/geodata/gisco/basic_services/"+service+"_"+year+"_3035.gpkg", bbox=bbox, where="levels IS NULL or levels!='0'" if service=="education" else "")

            # build accessibility grid
            accessiblity_grid_k_nearest_dijkstra_parallel(
                pois_loader = pois_loader,
                road_network_loader = road_network_loader,
                bbox = bbox,
                out_folder = out_folder_service_year,
                k = 3,
                weight_function = weight_function,
                direction_fun = direction_fun,
                is_not_snappable_fun = is_not_snappable_fun,
                initial_node_level_fun = initial_node_level_fun,
                final_node_level_fun = final_node_level_fun,
                cell_id_fun = cell_id_fun,
                grid_resolution= grid_resolution,
                cell_network_max_distance= grid_resolution * 2,
                file_size = file_size,
                extention_buffer = 20000 if service=="education" else 60000,
                detailled = detailled_network_decomposition,
                densification_distance=densification_distance,
                duration_simplification_fun = duration_simplification_fun,
                num_processors = num_processors_to_use,
                shuffle=True
            )

