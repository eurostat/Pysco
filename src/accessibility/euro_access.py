from math import floor
from accessiblity_grid_k_nearest_dijkstra import accessiblity_grid_k_nearest_dijkstra

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import iter_features
from utils.gpkg_to_geotiff import gpkg_grid_to_geotiff


#TODO
#TODO check paris centre bug - pedestrian areas
#TODO take private access sections - tracks
#TODO check ferries
#TODO school: exclude some...
#TODO school, by walking
#TODO ajouter code pays/nuts aux cellules
#TODO remove DE, RS, CH, etc.
#TODO handle case when speed depends on driving direction
#TODO euro_access


#set bbox for test area
#luxembourg
#bbox = [4030000, 2930000, 4060000, 2960000]
#big
#bbox = [3500000, 2000000, 4000000, 2500000]
#test
#bbox = [3800000, 2300000, 3900000, 2400000]
#whole europe
bbox = [ 1000000, 500000, 6000000, 5500000 ]


out_folder = '/home/juju/gisco/accessibility/'
gpkg_tile_file_size_m = 500000
grid_resolution = 100
year = "2023"

clamp = lambda v:floor(v/gpkg_tile_file_size_m)*gpkg_tile_file_size_m
[xmin,ymin,xmax,ymax] = [clamp(v) for v in bbox]


for service in ["education", "healthcare"]:

    num_processors_to_use = 7 if service == "education" else 5

    # ouput folder
    f = out_folder + "out_" + service + "/"
    if not os.path.exists(f): os.makedirs(f)

    #launch process for each GPKG tile file
    for x in range(xmin, xmax+1, gpkg_tile_file_size_m):
        for y in range(ymin, ymax+1, gpkg_tile_file_size_m):
            print("GPKG tile", x, y)

            #output file
            out_file = "euro_access_" + service + "_" + str(grid_resolution) + "m_" + str(x) + "_" + str(y)

            #check if output file was already produced
            if os.path.isfile(f + out_file + ".gpkg"):
                print(out_file, "already produced")
                continue

            # define parameter functions

            # driving direction
            def direction_fun(feature):
                d = feature['properties']['ONEWAY']
                if d==None or d=="": return 'both'
                if d=="FT": return 'forward'
                if d=="TF": return 'backward'
                print("Unexpected driving direction: ", d)
                return None

            def road_network_loader(bbox): return iter_features("/home/juju/geodata/tomtom/tomtom_"+year+"12.gpkg", bbox=bbox, where="ONEWAY ISNULL or ONEWAY != 'N'")
            def pois_loader(bbox): return iter_features("/home/juju/geodata/gisco/basic_services/"+service+"_"+year+"_3035.gpkg", bbox=bbox)
            def weight_function(feature, length): return -1 if feature['properties']['KPH']==0 else 1.1*length/feature['properties']['KPH']*3.6
            def cell_id_fun(x,y): return "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))
            def is_not_snappable_fun(f): return f['properties']['FOW'] in [1,10,12,6] or f['properties']['FREEWAY'] == 1
            def initial_node_level_fun(f): return f['properties']['F_ELEV']
            def final_node_level_fun(f): return f['properties']['T_ELEV']
            def duration_simplification_fun(x): return round(x,1)

            # build accessibility grid
            accessiblity_grid_k_nearest_dijkstra(
                pois_loader = pois_loader,
                road_network_loader = road_network_loader,
                bbox = [x, y, x+gpkg_tile_file_size_m, y+gpkg_tile_file_size_m],
                out_folder = f,
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
                partition_size = 125000,
                extention_buffer = 20000 if service=="education" else 60000,
                detailled = True,
                duration_simplification_fun = duration_simplification_fun,
                crs = 'EPSG:3035',
                num_processors_to_use = num_processors_to_use,
                save_GPKG = True,
                save_CSV = False,
                save_parquet = False
            )

    # GPKG to tiff
    if True:

        # get all GPKG files in the output folder
        gpkg_files = [os.path.join(f, f) for f in os.listdir(f) if f.endswith('.gpkg')]

        print("transforming", len(gpkg_files), "gpkg files into tif for", service)
        gpkg_grid_to_geotiff(
            gpkg_files,
            out_folder + "euro_access_" + service + "_" + year + "_" + str(grid_resolution) + "m.tif",
            attributes=["duration_1", "duration_average_3"],
            gpkg_nodata_values=[-1],
            compress='deflate'
        )

