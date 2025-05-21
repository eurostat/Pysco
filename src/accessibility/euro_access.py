from math import floor
from accessiblity_grid_k_nearest_dijkstra import accessiblity_grid_k_nearest_dijkstra

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import iter_features



#TODO handle case when speed depends on driving direction


#luxembourg
#bbox = [4030000, 2930000, 4060000, 2960000]
#big
bbox = [3500000, 2000000, 4000000, 2500000]
#test
#bbox = [3800000, 2300000, 3900000, 2400000]
#cnetral europe
bbox = [ 2500000, 1500000, 5500000, 3500000 ]


file_size_m = 500000
out_folder = '/home/juju/gisco/accessibility/out_partition/'

clamp = lambda v:floor(v/file_size_m)*file_size_m
[xmin,ymin,xmax,ymax] = [clamp(v) for v in bbox]

num_processors_to_use = 6
grid_resolution = 100

for service in ["education"]: #, "healthcare"]:

    #launch process for each tile file
    for x in range(xmin, xmax+1, file_size_m):
        for y in range(ymin, ymax+1, file_size_m):
            print(x,y)

            out_file = "euroaccess_" + service + "_" + str(grid_resolution) + "m_" + str(x) + "_" + str(y)
            partition_size = 125000
            extention_buffer = 20000 if service=="education" else 60000

            def direction_fun(feature):
                d = feature['properties']['ONEWAY']
                if d==None or d=="": return 'both'
                if d=="FT": return 'forward'
                if d=="TF": return 'backward'
                print("Unexpected driving direction: ", d)
                return None

            def road_network_loader(bbox): return iter_features("/home/juju/geodata/tomtom/tomtom_202312.gpkg", bbox=bbox, where="ONEWAY ISNULL or ONEWAY != 'N'")
            def pois_loader(bbox): return iter_features("/home/juju/geodata/gisco/basic_services/"+service+"_2023_3035.gpkg", bbox=bbox)
            def weight_function(feature, length): return -1 if feature['properties']['KPH']==0 else 1.1*length/feature['properties']['KPH']*3.6
            def cell_id_fun(x,y): return "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))
            def is_not_snappable_fun(f): return f['properties']['FOW'] in [1,10,12,6] or f['properties']['FREEWAY'] == 1
            def initial_node_level_fun(f): return f['properties']['F_ELEV']
            def final_node_level_fun(f): return f['properties']['T_ELEV']
            def duration_simplification_fun(x): return round(x,1)

            accessiblity_grid_k_nearest_dijkstra(
                pois_loader = pois_loader,
                road_network_loader = road_network_loader,
                bbox = [x, y, x+file_size_m, y+file_size_m],
                out_folder = out_folder,
                out_file = out_file,
                k = 3,
                weight_function = weight_function,
                direction_fun = direction_fun,
                is_not_snappable_fun = is_not_snappable_fun,
                initial_node_level_fun = initial_node_level_fun,
                final_node_level_fun = final_node_level_fun,
                cell_id_fun = cell_id_fun,
                grid_resolution= grid_resolution,
                cell_network_max_distance= grid_resolution * 1.5,
                partition_size = partition_size,
                extention_buffer = extention_buffer,
                detailled = True,
                duration_simplification_fun = duration_simplification_fun,
                crs = 'EPSG:3035',
                num_processors_to_use = num_processors_to_use,
                save_GPKG = True,
                save_CSV = False,
                save_parquet = True
            )

