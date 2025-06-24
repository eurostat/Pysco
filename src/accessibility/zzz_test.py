from accessiblity_grid_k_nearest_dijkstra import accessiblity_grid_k_nearest_dijkstra_parallel

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import iter_features
from utils.convert import parquet_grid_to_geotiff
from utils.geotiff import rename_geotiff_bands
from utils.tomtomutils import weight_function, direction_fun, is_not_snappable_fun, initial_node_level_fun, final_node_level_fun


#TODO add missing countries (DE) from internal data
#TODO check discontinuities ! SE, etc.
#TODO simplify - one file per parall process
#check: FEATTYP=4110 FRC 0 to 6
#TODO healthcare: new 2023 with new EL

#TODO QGIS plugin for parquet grids
#TODO handle case when speed depends on driving direction




#set bbox for test area
#luxembourg
bbox = [4030000, 2930000, 4060000, 2960000]
#big
#bbox = [3500000, 2000000, 4000000, 2500000]
#test
#bbox = [3800000, 2300000, 3900000, 2400000]
#whole europe
#bbox = [ 1000000, 500000, 7000000, 5500000 ]


grid_resolution = 100

def cell_id_fun(x,y): return "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))
def duration_simplification_fun(x): return int(round(x))


service = "education"

for year in ["2020"]: #"2023",

    tomtom_year = "2019" if year == "2020" else year
    def road_network_loader(bbox): return iter_features("/home/juju/geodata/tomtom/tomtom_"+tomtom_year+"12.gpkg", bbox=bbox)
    def pois_loader(bbox): return iter_features("/home/juju/geodata/gisco/basic_services/"+service+"_"+year+"_3035.gpkg", bbox=bbox, where="levels!='0'" if service=="education" else "")

    # build accessibility grid
    accessiblity_grid_k_nearest_dijkstra_parallel(
        pois_loader = pois_loader,
        road_network_loader = road_network_loader,
        bbox = bbox,
        out_parquet_file = "/home/juju/gisco/accessibility/grid_"+year+".parquet",
        k = 3,
        weight_function = weight_function,
        direction_fun = direction_fun,
        is_not_snappable_fun = is_not_snappable_fun,
        initial_node_level_fun = initial_node_level_fun,
        final_node_level_fun = final_node_level_fun,
        cell_id_fun = cell_id_fun,
        grid_resolution= grid_resolution,
        cell_network_max_distance= grid_resolution * 2,
        partition_size = 30000,
        extention_buffer = 10000,
        detailled = True,
        duration_simplification_fun = duration_simplification_fun,
        num_processors_to_use = 1,
    )

    print("Convert parquet to geotiff")
    parquet_grid_to_geotiff(
        ['/home/juju/gisco/accessibility/grid_'+year+'.parquet'],
        '/home/juju/gisco/accessibility/grid_'+year+'.tif',
        attributes=["duration_s_1", "duration_average_s_3"],
        parquet_nodata_values=[-1],
        compress='deflate'
    )

    print("Rename bands")
    rename_geotiff_bands('/home/juju/gisco/accessibility/grid_'+year+'.tif', [service+"_1_"+year, service+"_a3_"+year])

'''
combine_geotiffs(
    [
        "/home/juju/gisco/accessibility/grid_2020.tif",
        "/home/juju/gisco/accessibility/grid_2023.tif",
        "/home/juju/geodata/jrc/JRC_CENSUS_2021_100m_grid/JRC-CENSUS_2021_100m.tif"
     ],
    "/home/juju/gisco/accessibility/grid.tif",
    output_bounds=bbox,
    compress="deflate"
)
'''
