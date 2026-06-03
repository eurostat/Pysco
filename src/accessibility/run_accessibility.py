from accessiblity_grid_k_nearest_dijkstra import accessiblity_grid_k_nearest_dijkstra_parallel

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import iter_features
from utils.tomtomutils import weight_function, is_not_snappable_fun, initial_node_level_fun, final_node_level_fun, is_start_blocked, is_end_blocked
from datetime import datetime
import argparse

# Parameters
parser = argparse.ArgumentParser(description="Accessibility Processing")

# Paramètres de fichiers
parser.add_argument("--network", type=str, required=True, help="Path to network GPKG (Required) ")
parser.add_argument("--pois", type=str, required=True, help="Path to POI GPKG file (Required)")
parser.add_argument("--out_folder", type=str, required=True, help="Out Folder (Required)")

# Paramètres métier
parser.add_argument("--service", type=str, default='education', help="Type of service (default : education)")
parser.add_argument("--year", type=str, default='2023', help="Year (default : 2023)")

# Paramètres de la grille
parser.add_argument("--res", type=int, default=100, help="Grid resolution in meter (default : 100)")
parser.add_argument("--buff", type=int, default=20000, help="Buffer size in meter (default : 20000)")
parser.add_argument("--bbox", type=float, nargs=4, metavar=('xmin', 'ymin', 'xmax', 'ymax'),
                    default=[3590801, 2943207, 3691022, 3020024], help="Bounding box : xmin ymin xmax ymax")

# Paramètres techniques
parser.add_argument("--procs", type=int, help="Number of procs")
parser.add_argument("--file_size", type=int, default=10000, help="File size")

parser.add_argument("--is_shuffle", type=bool, default=True, help="Random processing")

args = parser.parse_args()

# Folder for Network 
#network_gpkg = "C:/_data/tomtom/tomtom202512_with_average_speed_v2_extract_for_testing.gpkg"
network_gpkg=args.network

#POI Folder
#pois_gpkg = "C:/_data/basic_services/education_2023_3035.gpkg"
pois_gpkg=args.pois
#type of service
# service='education'
service=args.service

#year
# year='2023'
year=args.year


#Output Folder
out_folder = 'C:/_data/accessibility_test/'
out_folder=args.out_folder

# define output bounding box
# bbox=[3590801,2943207,3691022,3020024]
bbox=args.bbox


#Grid resolution
# grid_resolution=100
grid_resolution=args.res

#File Size parameter
# tile file size, in m
#file_size = 200000 if grid_resolution == 100 else 500000
#file_size = 10000 if grid_resolution == 100 else 500000
# file_size=10000
file_size=args.file_size

is_shuffle=args.is_shuffle

# detailled network decomposition only when resolution to 100m
detailled_network_decomposition = grid_resolution == 100

# densification
densification_distance = grid_resolution

# keep cells whose centre is within 3 * grid_resolution from a network node
cell_network_max_distance = 3 * grid_resolution
                


def cell_id_fun(x,y): return "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))

def duration_simplification_fun(x): return int(round(x))


# choose number of processors, depending on service type and resolution
if grid_resolution == 100:
    num_processors_to_use = 5 if service == "education" else 3
else: num_processors_to_use = 10

# define tile buffer, depending on service type
# extention_buffer = 20000 if service=="education" else 60000
extention_buffer=args.buff

# define and create ouput folder, depending on year, service, resolution
out_folder_service_year = out_folder + "out_" + service + "_" + year + "_" + str(grid_resolution) + "m/"

if not os.path.exists(out_folder_service_year): os.makedirs(out_folder_service_year)

# define tomtom year
#tomtom_year = "2019" if year == "2020" else year

# define tomtom and POI loaders
#def road_network_loader(bbox): return iter_features(tomtom_data_folder + "tomtom"+tomtom_year+"12_with_average_speed_v2.gpkg", bbox=bbox) #, where="FOW!='20'"


def road_network_loader(bbox): return iter_features(network_gpkg, bbox=bbox) #, where="FOW!='20'"

def pois_loader(bbox): return iter_features(pois_gpkg, bbox=bbox) #, where="levels IS NULL or levels!='0'" if service=="education" else "")



if __name__ == '__main__':
    print("Launch function")
    startTime=datetime.now()
    print(startTime)

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
        cell_network_max_distance= grid_resolution * 2,
        file_size = file_size,
        extention_buffer = extention_buffer,
        detailled = detailled_network_decomposition,
        densification_distance=densification_distance,
        duration_simplification_fun = duration_simplification_fun,
        num_processors = num_processors_to_use,
        shuffle=is_shuffle,
        show_detailled_messages = True
    )

    EndTime=datetime.now()
    print("End")
    print("Duration : " +str(EndTime-startTime))


