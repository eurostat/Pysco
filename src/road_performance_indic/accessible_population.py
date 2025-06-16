from math import floor
from multiprocessing import Pool
import random
import numpy as np
import pandas as pd
from datetime import datetime
import sys
import os
import graph_tool.all as gt


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.utils import cartesian_product_comp
from utils.convert import parquet_grid_to_geotiff
from utils.netutils import ___graph_adjacency_list_from_geodataframe, distance_to_node, nodes_spatial_index_adjacendy_list
from utils.tomtomutils import direction_fun, final_node_level_fun, initial_node_level_fun, is_not_snappable_fun, weight_function
from utils.featureutils import iter_features
from utils.gridutils import get_cell_xy_from_id



def build_graph_tool_graph(graph):
    g = gt.Graph(directed=True)
    weight_prop = g.new_edge_property("double")

    # Map node ids to graph-tool vertex indices
    node_id_to_index = {}
    index_to_node_id = {}
    for node_id in graph.keys():
        v = int(g.add_vertex())
        node_id_to_index[node_id] = v
        index_to_node_id[v] = node_id

    # Add edges with weights
    for source_id, neighbors in graph.items():
        u_idx = node_id_to_index[source_id]
        for dest_id, w in neighbors:
            v_idx = node_id_to_index[dest_id]
            e = g.add_edge(u_idx, v_idx)
            weight_prop[e] = w

    return g, weight_prop, node_id_to_index, index_to_node_id




def accessiblity_population(xy,
            out_folder,
            duration_s,
            extention_buffer,
            file_size,
            road_network_loader,
            weight_function,
            direction_fun,
            is_not_snappable_fun,
            initial_node_level_fun,
            final_node_level_fun,
            grid_resolution,
            cell_network_max_distance = None,
            detailled = False,
            densification_distance = None,
            show_detailled_messages = False,
            cell_id_fun = lambda x,y : str(x)+"_"+str(y)
            ):

    # get position
    [ x_part, y_part ] = xy

    # output file
    out_file = out_folder + "ap_" + str(grid_resolution) + "m_" + str(x_part) + "_" + str(y_part) + ".parquet"
    # skip if output file was already produced
    if os.path.isfile(out_file): return

    if not show_detailled_messages: print(datetime.now(), x_part, y_part)

    # build extended bbox
    extended_bbox = (x_part-extention_buffer, y_part-extention_buffer, x_part+file_size+extention_buffer, y_part+file_size+extention_buffer)

    if show_detailled_messages: print(datetime.now(), x_part, y_part, "make graph")
    roads = road_network_loader(extended_bbox)
    gb_ = ___graph_adjacency_list_from_geodataframe(roads,
                                                        weight_fun = weight_function,
                                                        direction_fun = direction_fun,
                                                        is_not_snappable_fun = is_not_snappable_fun,
                                                        detailled = detailled,
                                                        densification_distance = densification_distance,
                                                        initial_node_level_fun = initial_node_level_fun,
                                                        final_node_level_fun = final_node_level_fun )
    graph = gb_['graph']
    snappable_nodes = gb_['snappable_nodes']
    del gb_, roads
    if show_detailled_messages: print(datetime.now(), x_part, y_part, len(graph.keys()), "nodes,", len(snappable_nodes), "snappable nodes.")
    #if(len(snappable_nodes)==0): return

    if show_detailled_messages: print(datetime.now(), x_part, y_part, "build graph-tool graph")
    graph, weight_prop, node_id_to_index, index_to_node_id = build_graph_tool_graph(graph)

    if show_detailled_messages: print(datetime.now(), x_part, y_part, "build nodes spatial index")
    idx = nodes_spatial_index_adjacendy_list(snappable_nodes)

    # dictionnary that assign population to graph node
    node_pop_dict = {}

    if show_detailled_messages: print(datetime.now(), x_part, y_part, "Project population grid on graph nodes")
    cells = population_grid_loader(extended_bbox)
    r2 = grid_resolution/2
    for c in cells:
        c = c['properties']
        pop = c['T']
        if pop is None or pop == 0: continue

        id = c['GRD_ID']
        x,y = get_cell_xy_from_id(id)
        x+=r2
        y+=r2

        # get closest graph snappable node
        ni = next(idx.nearest((x, y, x, y), 1), None)
        if ni == None:
            print("Could not find network node for grid cell", id)
            continue
        n = snappable_nodes[ni]
        if n in node_pop_dict: node_pop_dict[n] += pop
        else: node_pop_dict[n] = pop

        # store populated cells within the bbox
        #if x>=x_part and y>=y_part and x<x_part+partition_size and y<y_part+partition_size:
        #    populated_cells.append((id,x,y))
    del cells

    # destination nodes: all nodes with population - get destination indices as a numpy array - it is faster
    populated_nodes = node_pop_dict.keys()
    #if show_detailled_messages: print(datetime.now(), x_part, y_part, "prepare populated nodes")
    #dest_indices = np.array([node_id_to_index[dest_id] for dest_id in populated_nodes if dest_id in node_id_to_index], dtype=np.int32)
    # index graph vertexes by populated node codes
    graph_id_to_vertex = {}
    for nn in populated_nodes: graph_id_to_vertex[nn] = graph.vertex(node_id_to_index[nn])
    # create numpy arrays for lookups
    populated_vertex_indices = np.array([graph_id_to_vertex[nn] for nn in populated_nodes], dtype=np.int64)
    populated_pops = np.array([node_pop_dict[nn] for nn in populated_nodes], dtype=np.int64)
    del graph_id_to_vertex

    # output data
    grd_ids = [] # the cell identifiers
    accessible_populations = [] # the values corresponding to the cell identifiers

    # a cache structure, to ensure there is no double computation for some nodes. it could happen, since some cells may snap to a same graph node
    cache = {}

    if len(snappable_nodes)>0:

        # go through cells
        if show_detailled_messages: print(datetime.now(), x_part, y_part, "compute routing")
        r2 = grid_resolution / 2
        for x in range(x_part, x_part+file_size, grid_resolution):
            #print(datetime.now(), x)
            for y in range(y_part, y_part+file_size, grid_resolution):
            #for pc in populated_cells:
                #id, x, y = pc
                #print(datetime.now(),"start")

                # snap cell centre to the snappable nodes, using the spatial index
                ni_ = next(idx.nearest((x+r2, y+r2, x+r2, y+r2), 1), None)
                if ni_ == None:
                    print(datetime.now(), x_part, y_part, "graph node not found for cell", x,y)
                    continue
                n = snappable_nodes[ni_]

                # compute distance from cell centre to node, and skip if too far
                dtn = distance_to_node(n, x+r2, y+r2)
                if cell_network_max_distance is not None and cell_network_max_distance>0 and dtn>= cell_network_max_distance: continue

                # check if value was not already computed - try to find it in the cache
                if n in cache:
                    #print("Node found in cache", n, cache[n])
                    accessible_populations.append(cache[n])
                    grd_ids.append(cell_id_fun(x,y))
                    continue

                # get origin node index
                origin_idx = node_id_to_index[n]

                # compute dijkstra
                #print(datetime.now())
                dist_map = gt.shortest_distance(graph, source=graph.vertex(origin_idx), weights=weight_prop, max_dist=duration_s)
                #print(datetime.now())

                #check node n is reached
                #print("origin node:", dist_map[graph.vertex(origin_idx)])

                '''
                sum_pop = 0
                inf = float('inf')
                for nn in populated_nodes:
                    dist = dist_map[graph_id_to_vertex[nn]]
                    if dist < inf:
                        # check node is in list
                        #if nn == n: print("ok", dist)
                        sum_pop += node_pop_dict[nn]

                print(sum_pop)
                '''

                # compute population sum for reached nodes
                dist_arr = dist_map.get_array()
                reachable_mask = dist_arr[populated_vertex_indices] < np.inf
                sum_pop = np.sum(populated_pops[reachable_mask])

                # store cell value
                accessible_populations.append(sum_pop)
                grd_ids.append(cell_id_fun(x,y))

                # cache value, to be sure is is not computed another time
                cache[n] = sum_pop
                #print(datetime.now(),"end")

    # save output as parquet
    data = { 'GRD_ID':grd_ids, 'ACC_POP_1H30':accessible_populations }
    pd.DataFrame(data).to_parquet(out_file)

    print(datetime.now(), x_part, y_part, len(grd_ids), "cells saved")




def accessiblity_population_parallel(
                       road_network_loader,
                       bbox,
                       out_folder,
                       duration_s,
                       weight_function = lambda feature,sl:sl,
                       direction_fun=lambda feature:"both", #('both', 'oneway', 'forward', 'backward')
                       is_not_snappable_fun = None,
                       initial_node_level_fun=None,
                       final_node_level_fun=None,
                       cell_id_fun=lambda x,y:str(x)+"_"+str(y),
                       grid_resolution=1000,
                       cell_network_max_distance=-1,
                       file_size = 100000,
                       extention_buffer = 30000,
                       detailled = False,
                       densification_distance = None,
                       num_processors_to_use = 1,
                       show_detailled_messages = False,
                       shuffle = True,
                       ):

    # launch parallel computation   
    processes_params = cartesian_product_comp(bbox[0], bbox[1], bbox[2], bbox[3], file_size)
    if shuffle: random.shuffle(processes_params)

    processes_params = [
        (
            xy,
            out_folder,
            duration_s,
            extention_buffer,
            file_size,
            road_network_loader,
            weight_function,
            direction_fun,
            is_not_snappable_fun,
            initial_node_level_fun,
            final_node_level_fun,
            grid_resolution,
            cell_network_max_distance,
            detailled,
            densification_distance,
            show_detailled_messages,
            cell_id_fun
        )
        for xy in processes_params
        ]

    print(datetime.now(), "launch", len(processes_params), "processes on", num_processors_to_use, "processor(s)")
    Pool(num_processors_to_use).starmap(accessiblity_population, processes_params)




#TODO check bug - why discontinuities ?
#TODO test 100m ?
#TODO compute population <1H30 AND < 120km


# where to store the outputs
out_folder = '/home/juju/gisco/road_transport_performance/'

grid_resolution = 1000
detailled = False
densification_distance = grid_resolution
shuffle = True
show_detailled_messages = False


# define output bounding box
# whole europe
bbox = [ 900000, 900000, 6600000, 5400000 ]
#luxembourg
#bbox = [4030000, 2930000, 4060000, 2960000]
#greece
#bbox = [ 5000000, 1500000, 5500000, 2000000 ]

file_size = 200000
extention_buffer = 180000 # 180000
duration_s = 60 * 90 #1h30=90min
num_processors_to_use = 6

def population_grid_loader_2021(bbox): return iter_features("/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg", bbox=bbox)
def cell_id_fun(x,y): return "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))


for year in ["2021"]:

    # ouput folder
    out_folder_year = out_folder + "out_" + year + "_" + str(grid_resolution) + "m/"
    if not os.path.exists(out_folder_year): os.makedirs(out_folder_year)

    tomtom_year = "2023" if year == "2021" else None
    def road_network_loader(bbox): return iter_features("/home/juju/geodata/tomtom/tomtom_"+tomtom_year+"12.gpkg", bbox=bbox, where="NOT(FOW==-1 AND FEATTYP==4130)")
    population_grid_loader = population_grid_loader_2021 if year == "2021" else None

    if True:
        accessiblity_population_parallel(
                            road_network_loader,
                            bbox = bbox,
                            out_folder = out_folder_year,
                            duration_s = duration_s,
                            weight_function = weight_function,
                            direction_fun = direction_fun,
                            is_not_snappable_fun = is_not_snappable_fun,
                            initial_node_level_fun = initial_node_level_fun,
                            final_node_level_fun = final_node_level_fun,
                            cell_id_fun = cell_id_fun,
                            grid_resolution = grid_resolution,
                            cell_network_max_distance = grid_resolution * 2,
                            file_size = file_size,
                            extention_buffer = extention_buffer,
                            detailled = detailled,
                            densification_distance = densification_distance,
                            num_processors_to_use = num_processors_to_use,
                            shuffle = shuffle,
                            show_detailled_messages = show_detailled_messages,
                            )

    # combine parquet files to a single tiff file
    geotiff = out_folder + "accessible_population_" + year + "_" + str(grid_resolution) + "m.tif"

    # check if tiff file was already produced
    #if os.path.isfile(geotiff): continue

    # get all parquet files in the output folder
    files = [os.path.join(out_folder_year, f) for f in os.listdir(out_folder_year) if f.endswith('.parquet')]
    if len(files)==0: continue

    print("transforming", len(files), "parquet files into tif for", year)
    parquet_grid_to_geotiff(
        files,
        geotiff,
        bbox = bbox,
        dtype=np.int32,
        compress='deflate'
    )
