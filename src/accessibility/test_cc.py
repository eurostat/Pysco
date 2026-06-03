from accessiblity_grid_k_nearest_dijkstra import accessiblity_grid_k_nearest_dijkstra
import pandas as pd
import numpy as np

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import iter_features
from utils.tomtomutils import weight_function, is_not_snappable_fun, initial_node_level_fun, final_node_level_fun, is_start_blocked, is_end_blocked
from utils.convert import parquet_grid_to_geotiff



# folders where to store the outputs
out_folder = '/home/juju/Bureau/test_cc/'
out_file = out_folder + "100m_3930000_2250000.parquet"
if not os.path.exists(out_folder): os.makedirs(out_folder)

bbox = [ 3930000, 2250000,  3960000, 2280000 ]
grid_resolution = 100
year = "2023"

# build accessibility grid
if True:

    if os.path.exists(out_file): os.remove(out_file)

    def road_network_loader(bbox): return iter_features("/home/juju/geodata/tomtom/tomtom202312.gpkg", bbox=bbox) #, where="FOW!='20'"
    def pois_loader(bbox): return iter_features("/home/juju/geodata/gisco/basic_services/healthcare_2023_3035_20260421"+".gpkg", bbox=bbox) #, where="levels IS NULL or levels!='0'" if service=="education" else "")

    data = accessiblity_grid_k_nearest_dijkstra(
        pois_loader = pois_loader,
        road_network_loader = road_network_loader,
        bbox = bbox,
        k = 3,
        weight_function = weight_function,
        is_not_snappable_fun = is_not_snappable_fun,
        initial_node_level_fun = initial_node_level_fun,
        is_start_blocked = is_start_blocked,
        is_end_blocked = is_end_blocked,
        final_node_level_fun = final_node_level_fun,
        cell_id_fun = lambda x,y: "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x)),
        grid_resolution= grid_resolution,
        cell_network_max_distance= 1000,
        to_network_speed_ms= 15/3.6,
        detailled = True,
        densification_distance=100,
        cost_simplification_fun = lambda x: int(round(x)),
        show_detailled_messages = True
    )

    print("nb lines", len(data))

    # save as parquet
    pd.DataFrame(data).to_parquet(out_file)


if True:
    print("to_geotiff")
    parquet_grid_to_geotiff(
        [out_file],
        out_folder + "out.tiff",
        bbox = bbox,
        attributes=["cost_s_1", "cost_average_s_3"],
        parquet_nodata_values=[-1],
        dtype=np.int16,
        value_fun= lambda v:v if v<32767 else 32767, # np.int16(v),
        compress='deflate'
    )

