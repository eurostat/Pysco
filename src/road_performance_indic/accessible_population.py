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
from utils.netutils import ___graph_adjacency_list_from_geodataframe, distance_to_node, node_coordinate, nodes_spatial_index_adjacendy_list
from utils.tomtomutils import direction_fun, final_node_level_fun, initial_node_level_fun, is_not_snappable_fun, weight_function
from utils.featureutils import iter_features
from utils.gridutils import get_cell_xy_from_id
from utils.geotiff import read_geotiff_pixels_as_dicts


'''
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
'''


def build_graph_tool_graph_fast(graph):
    g = gt.Graph(directed=True)
    N = len(graph)
    g.add_vertex(N)  # preallocate all vertices at once

    # Map node ids to consecutive indices
    node_id_list = list(graph.keys())
    node_id_to_index = {node_id: idx for idx, node_id in enumerate(node_id_list)}
    index_to_node_id = {idx: node_id for idx, node_id in enumerate(node_id_list)}

    # Collect edges and weights
    edge_list = []
    weights = []
    for source_id, neighbors in graph.items():
        u_idx = node_id_to_index[source_id]
        for dest_id, w in neighbors:
            v_idx = node_id_to_index[dest_id]
            edge_list.append((u_idx, v_idx))
            weights.append(w)

    # Add all edges in bulk
    g.add_edge_list(edge_list)

    # Assign weights
    weight_prop = g.new_edge_property("double")
    for e, w in zip(g.edges(), weights):
        weight_prop[e] = w

    return g, weight_prop, node_id_to_index, index_to_node_id







def accessiblity_population(xy,
            out_folder,
            duration_max_s,
            distance_max_m,
            extention_buffer,
            file_size,
            road_network_loader,
            population_grid_loader,
            pop_col,
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

    # output data
    grd_ids = [] # the cell identifiers
    accessible_populations = [] # the values corresponding to the cell identifiers
    near_accessible_populations = [] # the values corresponding to the cell identifiers

    if len(snappable_nodes) == 0:
        pd.DataFrame({}).to_parquet(out_file)
        print(datetime.now(), x_part, y_part, "0 cells saved")
        return

    if show_detailled_messages: print(datetime.now(), x_part, y_part, "build graph-tool graph")
    graph, weight_prop, node_id_to_index, index_to_node_id = build_graph_tool_graph_fast(graph)

    if show_detailled_messages: print(datetime.now(), x_part, y_part, "build nodes spatial index")
    idx = nodes_spatial_index_adjacendy_list(snappable_nodes)

    # dictionnary that assign population to graph node
    node_pop_dict = {}

    if show_detailled_messages: print(datetime.now(), x_part, y_part, "Project population grid on graph nodes")
    cells = population_grid_loader(extended_bbox)
    r2 = grid_resolution/2
    for c in cells:
        x = c['x']
        y = c['y']
        pop = c['value']
        '''
        c = c['properties']
        pop = c[pop_col]
        if pop is None or pop == 0: continue

        id = c['GRD_ID']
        x,y = get_cell_xy_from_id(id)
        '''
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

    del cells

    # destination nodes: all nodes with population
    #populated_nodes = node_pop_dict.keys()

    # index graph vertexes by populated node codes
    #graph_id_to_vertex = {}
    #for nn in populated_nodes: graph_id_to_vertex[nn] = graph.vertex(node_id_to_index[nn])

    # create numpy arrays for lookups
    # list of graph vertex indices with some population
    populated_graph_vertex_indices = np.array([graph.vertex(node_id_to_index[nn]) for nn in node_pop_dict.keys()], dtype=np.int64)

    # population of these nodes, same order
    #populated_pops = np.array([node_pop_dict[nn] for nn in populated_nodes], dtype=np.int64)
    populated_pops = np.array(list(node_pop_dict.values()), dtype=np.int64)

    # clean
    #del graph_id_to_vertex
    #del populated_nodes
    del node_pop_dict

    # a cache structure, to ensure there is no double computation for some nodes. it could happen, since some cells may snap to a same graph node
    cache = {}

    # go through cells
    if show_detailled_messages: print(datetime.now(), x_part, y_part, "compute accessible population by cell")
    r2 = grid_resolution / 2


    '''
    def is_within_distance(xo, yo, dest_idx):
        nd = index_to_node_id[dest_idx]
        x,y = node_coordinate(nd)
        #out = np.hypot(xo-x, yo-y) <= distance_max_m
        #if out: print(np.hypot(xo-x, yo-y), nd)
        return np.hypot(xo-x, yo-y) <= distance_max_m
    '''

    '''
    # pre-compute node (x,y)
    node_positions = {}
    for idx__ in index_to_node_id.keys():
        node_positions[idx__] = node_coordinate(index_to_node_id[idx__])
    '''

    '''
    def get_is_within_distance_fun(xo, yo):
        def is_within_distance(dest_idx):
            #nd = index_to_node_id[dest_idx]
            #x,y = node_coordinate(nd)
            x,y = node_positions[dest_idx]
            return np.hypot(xo-x, yo-y) <= distance_max_m
        return is_within_distance
    '''

    for x in range(x_part, x_part+file_size, grid_resolution):
        for y in range(y_part, y_part+file_size, grid_resolution):
            #print(datetime.now(), "*******")

            # snap cell centre to the graph snappable nodes, using the spatial index
            ni_ = next(idx.nearest((x+r2, y+r2, x+r2, y+r2), 1), None)
            if ni_ == None: raise(datetime.now(), x_part, y_part, "graph node not found for cell", x,y)
            n = snappable_nodes[ni_]

            # compute distance from cell centre to node, and skip if too far
            dtn = distance_to_node(n, x+r2, y+r2)
            if cell_network_max_distance is not None and cell_network_max_distance>0 and dtn>= cell_network_max_distance: continue

            # check if value was not already computed - try to find it in the cache
            if n in cache:
                # no need to compute another time: take cached value
                sum_pop, sum_pop2 = cache[n]
                accessible_populations.append(sum_pop)
                near_accessible_populations.append(sum_pop2)
                grd_ids.append(cell_id_fun(x,y))
                continue

            # get origin node index
            origin_idx = node_id_to_index[n]
            # xo,yo = node_coordinate(n)

            # compute dijkstra from origin, with cutoff
            #print(datetime.now(), "dijskra")
            # VertexPropertyMap of type double, where dist_map[v] gives the shortest distance from the source vertex origin_idx to vertex v
            dist_map = gt.shortest_distance(graph, source=graph.vertex(origin_idx), weights=weight_prop, max_dist=duration_max_s)

            #check node n is reached. value should be 0. OK
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

            # NumPy array view of the values stored in dist_map.
            # where each position i contains the distance from source vertex to vertex i.
            # The array follows the order of internal vertex indices (v such that int(v) == i).
            # Values are inf for vertices unreachable within max_dist
            #print(datetime.now(), "get arry")
            dist_arr = dist_map.get_array()

            # compute population within duration_max_s
            # dist_arr[populated_graph_vertex_indices] selects the distances to populated vertices.
            # < np.inf returns a boolean array: True for each vertex in the selection if its distance is finite.
            #print(datetime.now(), "sum pop")
            reachable_mask = dist_arr[populated_graph_vertex_indices] < np.inf
            sum_pop = np.sum(populated_pops[reachable_mask])

            '''
            # compute population within duration_max_s and distance_max_m
            #print(datetime.now(), "sum pop2")
            is_within_distance = get_is_within_distance_fun(xo, yo)
            distance_mask = np.array([is_within_distance(idx_) for idx_ in populated_graph_vertex_indices])
            combined_mask = reachable_mask & distance_mask
            sum_pop2 = np.sum(populated_pops[combined_mask])
            #print(datetime.now(), "-")

            if sum_pop != sum_pop2: print(sum_pop2 / sum_pop, sum_pop2, sum_pop)
            '''
            sum_pop2 = 0


            # store cell value
            accessible_populations.append(sum_pop)
            near_accessible_populations.append(sum_pop2)
            grd_ids.append(cell_id_fun(x,y))

            # cache value, to be sure is is not computed another time
            cache[n] = [ sum_pop, sum_pop2 ]
            #print(datetime.now(),"end")

    # save output as parquet
    data = { 'GRD_ID':grd_ids, 'ACC_POP_1H30':accessible_populations } #, 'ACC_POP_1H30_120KM':near_accessible_populations }
    pd.DataFrame(data).to_parquet(out_file)

    print(datetime.now(), x_part, y_part, len(grd_ids), "cells saved")




def accessiblity_population_parallel(
                       road_network_loader,
                       population_grid_loader,
                       pop_col,
                       bbox,
                       out_folder,
                       duration_max_s,
                       distance_max_m,
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
            duration_max_s,
            distance_max_m,
            extention_buffer,
            file_size,
            road_network_loader,
            population_grid_loader,
            pop_col,
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

    print(datetime.now(), "launch", len(processes_params), "process(es) on", num_processors_to_use, "processor(s)")
    Pool(num_processors_to_use).starmap(accessiblity_population, processes_params)


#TODO compare figures
#TODO compute population <1H30 AND < 120km: not necessary ? All<100. Compare with regio why.
#TODO check places with index>100: islands connected with bridge - should be connected !
#TODO check and fix 2018-2021 inconsistencies

#TODO take right tomtom versions - 2018 and 2021 ?
#TODO 2011 version ?
#TODO test 100m ?



# where to store the outputs
out_folder = '/home/juju/gisco/road_transport_performance/'

grid_resolution = 1000
detailled = False
densification_distance = grid_resolution
shuffle = True
show_detailled_messages = True


# define output bounding box
# whole europe
bbox = [ 900000, 900000, 6600000, 5500000 ]
#luxembourg
#bbox = [4030000, 2930000, 4060000, 2960000]
#greece
#bbox = [ 5000000, 1500000, 5500000, 2000000 ]
#SW lisbon
#bbox = [ 2600000, 1900000, 2700000, 2000000 ]
# amsterdam
#bbox = [ 3900000, 3200000, 4000000, 3300000 ]


file_size = 200000 # 200000
extention_buffer = 180000 # 180000
duration_max_s = 90 * 60 #1h30=90min
distance_max_m = 120 * 1000 #120km
num_processors_to_use = 9

def population_grid_loader_2021(bbox): return read_geotiff_pixels_as_dicts(out_folder+"population_2021.tif", bbox=bbox, value_criteria_fun=lambda v:v>0)
def population_grid_loader_2018(bbox): return read_geotiff_pixels_as_dicts(out_folder+"population_2018.tif", bbox=bbox, value_criteria_fun=lambda v:v>0)
def cell_id_fun(x,y): return "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))

for year in ["2021", "2018"]:

    # ouput folder
    out_folder_year = out_folder + "out_" + year + "_" + str(grid_resolution) + "m/"
    if not os.path.exists(out_folder_year): os.makedirs(out_folder_year)

    tomtom_year = "2023" if year == "2021" else "2019"
    def road_network_loader(bbox): return iter_features("/home/juju/geodata/tomtom/tomtom_"+tomtom_year+"12.gpkg", bbox=bbox, where="NOT(FOW=-1 AND FEATTYP=4130)")

    accessiblity_population_parallel(
                        road_network_loader,
                        population_grid_loader_2021 if year == "2021" else population_grid_loader_2018,
                        'T' if year == "2021" else "TOT_P_2018",
                        bbox = bbox,
                        out_folder = out_folder_year,
                        duration_max_s = duration_max_s,
                        distance_max_m = distance_max_m,
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

