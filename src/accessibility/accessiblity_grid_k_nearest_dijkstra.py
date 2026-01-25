import random
import pandas as pd
from datetime import datetime
import heapq
from multiprocessing import Pool
from math import floor

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.utils import cartesian_product_comp
from utils.netutils import nodes_spatial_index_adjacendy_list, distance_to_node, ___graph_adjacency_list_from_geodataframe


def ___multi_source_k_nearest_dijkstra(graph, sources, k=3, with_paths=False):
    """
    Computes the k nearest sources, their costs, and optionally paths to each node.

    :param graph: A dictionary representing the adjacency list of the graph - that is each node is a key; and each value is a list of tuples (node,weight) of the links from this node.
    :param sources: A list of source node ids.
    :param k: Number of nearest sources to track.
    :param with_paths: Whether to track and return the paths.
    :return: A dictionary mapping each node to a sorted list of 
             {'cost': c, 'source': s, 'path': [sequence of nodes]} if with_paths,
             or {'cost': c, 'source': s} if not.
    """

    result = {node: [] for node in graph}
    priority_queue = []

    # Initialize all sources
    for source in sources:
        path = [source] if with_paths else None
        heapq.heappush(priority_queue, (0, source, source, path))  # (cost, current_node, origin_source, path)

    while priority_queue:
        current_cost, current_node, origin, path = heapq.heappop(priority_queue)

        # Check if we've already found k closest sources for this node
        current_sources = [entry['source'] for entry in result[current_node]]
        if origin in current_sources: continue  # Avoid duplicate source per node

        if len(result[current_node]) >= k: continue

        # Record this source, cost, and optional path
        entry = {
            'cost': current_cost,
            'source': origin
        }
        if with_paths:
            entry['path'] = path

        result[current_node].append(entry)

        # Visit neighbors
        for neighbor, weight in graph[current_node]:
            cost = current_cost + weight
            next_path = path + [neighbor] if with_paths else None
            heapq.heappush(priority_queue, (cost, neighbor, origin, next_path))

    # Sort lists by cost for each node
    for node in result:
        result[node].sort(key=lambda x: x['cost'])

    return result







def accessiblity_grid_k_nearest_dijkstra(xy,
            extention_buffer,
            file_size,
            out_folder,
            pois_loader,
            road_network_loader,
            k,
            weight_function,
            is_not_snappable_fun,
            initial_node_level_fun,
            final_node_level_fun,
            is_start_blocked,
            is_end_blocked,
            cell_id_fun,
            grid_resolution,
            cell_network_max_distance,
            to_network_speed_ms,
            detailled,
            densification_distance,
            duration_simplification_fun,
            keep_distance_to_node,
            show_detailled_messages = False,
            ):
    """ see accessiblity_grid_k_nearest_dijkstra_parallel below """

    # get position
    [ x_part, y_part ] = xy

    # output file
    out_file = out_folder + str(grid_resolution) + "m_" + str(x_part) + "_" + str(y_part) + ".parquet"
    # skip if output file was already produced
    if os.path.isfile(out_file): return

    print(datetime.now(), x_part, y_part)

    # build extended bbox
    extended_bbox = (x_part-extention_buffer, y_part-extention_buffer, x_part+file_size+extention_buffer, y_part+file_size+extention_buffer)

    if show_detailled_messages: print(datetime.now(), x_part, y_part, "get source POIs")
    pois = pois_loader(extended_bbox)
    if(not pois):
        pd.DataFrame({}).to_parquet(out_file)
        print(datetime.now(), x_part, y_part, "0 cells saved")
        return

    if show_detailled_messages: print(datetime.now(), x_part, y_part, "make graph")
    roads = road_network_loader(extended_bbox)
    gb_ = ___graph_adjacency_list_from_geodataframe(roads,
                                                        weight_fun = weight_function,
                                                        is_not_snappable_fun = is_not_snappable_fun,
                                                        detailled = detailled,
                                                        densification_distance=densification_distance,
                                                        initial_node_level_fun = initial_node_level_fun,
                                                        final_node_level_fun = final_node_level_fun,
                                                        is_start_blocked = is_start_blocked,
                                                        is_end_blocked = is_end_blocked,
                                                        )
    graph = gb_['graph']
    snappable_nodes = gb_['snappable_nodes']
    del gb_, roads
    if show_detailled_messages: print(datetime.now(), x_part, y_part, len(graph.keys()), "nodes,", len(snappable_nodes), "snappable nodes.")


    # TODO insert connex component logic here


    if(len(snappable_nodes)==0):
        pd.DataFrame({}).to_parquet(out_file)
        print(datetime.now(), x_part, y_part, "0 cells saved")
        return

    if show_detailled_messages: print(datetime.now(), x_part, y_part, "build nodes spatial index")
    idx = nodes_spatial_index_adjacendy_list(snappable_nodes)

    if show_detailled_messages: print(datetime.now(), x_part, y_part, "get source nodes")
    sources = []
    for poi in pois:
        x, y = poi['geometry']['coordinates']
        n = snappable_nodes[next(idx.nearest((x, y, x, y), 1))]
        sources.append(n)
    del pois
    if show_detailled_messages: print(datetime.now(), x_part, y_part, len(sources), "source nodes found")

    if show_detailled_messages: print(datetime.now(), x_part, y_part, "compute accessiblity")
    result = ___multi_source_k_nearest_dijkstra(graph=graph, k=k, sources=sources, with_paths=False)
    del graph, sources

    if show_detailled_messages: print(datetime.now(), x_part, y_part, "extract cell accessibility data")
    grd_ids = [] #the cell identifiers
    costs = [] #the costs - an array of arrays
    for _ in range(k): costs.append([])
    distances_to_node = [] #the cell center distance to its graph node

    # go through cells
    r2 = grid_resolution / 2
    for x in range(x_part, x_part+file_size, grid_resolution):
        for y in range(y_part, y_part+file_size, grid_resolution):

            # snap cell centre to the snappable nodes, using the spatial index
            ni_ = next(idx.nearest((x+r2, y+r2, x+r2, y+r2), 1), None)
            if ni_ == None: continue
            n = snappable_nodes[ni_]

            # compute distance from cell centre to node, and skip if too far
            dtn = distance_to_node(n, x+r2, y+r2)
            if cell_network_max_distance>0 and dtn>= cell_network_max_distance: continue

            # get costs
            cs = result[n]

            # add some cost for dtn travel
            ttn = 0
            if to_network_speed_ms is not None and to_network_speed_ms >0:
                ttn = dtn / to_network_speed_ms

            # store costs
            for kk in range(k):
                if kk>=len(cs): costs[kk].append(-1)
                else: costs[kk].append(cs[kk]['cost'] + ttn)

            # store distance cell center/node
            if keep_distance_to_node:
                distances_to_node.append( round(dtn) )

            # store cell id
            grd_ids.append(cell_id_fun(x,y))

    del result, idx, snappable_nodes

    if len(grd_ids) == 0:
        pd.DataFrame({}).to_parquet(out_file)
        print(datetime.now(), x_part, y_part, "0 cells saved")
        return

    # make output dataframe
    data = { 'GRD_ID':grd_ids }
    if keep_distance_to_node: data['distance_to_node'] = distances_to_node
    for kk in range(k): data['duration_s_'+str(kk+1)] = costs[kk]

    # compute average duration and simplify duration values
    averages = []
    for i in range(len(data['GRD_ID'])):
        # compute average
        sum = 0
        for kk in range(k):
            dur = data['duration_s_'+str(kk+1)][i]
            if dur<0: sum = -1; break
            sum += dur
            # simplify duration values
            if duration_simplification_fun != None: data['duration_s_'+str(kk+1)][i] = duration_simplification_fun(dur)
        # store average value, simplified if necessary
        if sum <0:
            sum = -1
        else:
            sum = sum/k
            if duration_simplification_fun != None: sum = duration_simplification_fun(sum)
        averages.append(sum)
    data['duration_average_s_'+str(k)] = averages

    # save output
    pd.DataFrame(data).to_parquet(out_file)

    print(datetime.now(), x_part, y_part, len(grd_ids), "cells saved")






def accessiblity_grid_k_nearest_dijkstra_parallel(
        pois_loader,
        road_network_loader,
        bbox,
        out_folder,
        k = 3,
        weight_function = lambda feature,sl:sl,
        is_not_snappable_fun = None,
        initial_node_level_fun=None,
        final_node_level_fun=None,
        is_start_blocked = None,
        is_end_blocked = None,
        cell_id_fun=lambda x,y:str(x)+"_"+str(y),
        grid_resolution=1000,
        cell_network_max_distance=-1,
        to_network_speed_ms = None,
        file_size = 100000,
        extention_buffer = 30000,
        detailled = False,
        densification_distance = None,
        duration_simplification_fun = None,
        keep_distance_to_node = False,
        num_processors = 1,
        show_detailled_messages = False,
        shuffle = False,
        ):
    """
    Compute accessiblity grid using k-nearest dijkstra algorithm.

    Args:
        pois_loader (fun): the POIs loader.
        road_network_loader (fun): the road network sections loader.
        bbox (bounding box): the bounding box to restrict the analysis.
        out_folder (str): the output folder path where to create the output parquet files, one per tile.
        k (int, optional): the k parmeter, to compute the average time to k nearest pois. Defaults to 3.
        weight_function (fun, optional): a function returning the weight of a network section part. Defaults to lambdafeature.
        direction_fun (fun, optional): a function returning the direction of a network section. Defaults to lambda feature:"both".
        is_not_snappable_fun (fun, optional): a function specifying the network sections that should not be used to snap cell centres. These are network sections that are forbidden to be used as origin/destination such as highway sections or access lanes.
        initial_node_level_fun (_type_, optional): a function returning the section initial node level code, to manage properly multi-level intersections. Defaults to None.
        final_node_level_fun (_type_, optional): a function returning the section final node level code, to manage properly multi-level intersections. Defaults to None.
        cell_id_fun (_type_, optional): a function returning the output grid cell code. Defaults to lambda x+y.
        grid_resolution (int, optional): the output grid resolution. Defaults to 1000.
        cell_network_max_distance (int, optional): the maximum distance from a cell centre to a network node. cells too far away from the network are ignored. Defaults to -1.
        to_network_speed_ms (int, optional): The speed to take into account to travel from cell centre to nearest network node. Set to None if the speed is infinite (exact snapping).
        file_size (int, optional): the size of each tile file. the larger, the fewer file but the more intensive. Defaults to 100000.
        extention_buffer (int, optional): the buffer distance around the tile area. The network and pois within the tile extended by this distance is loaded. Data only for the cell within the tile are stored. Defaults to 30000.
        detailled (bool, optional): Set to true to create a network node for each network section geometry vertice. Set to false to create nodes only for the initial and final nodes. Defaults to False.
        densification_distance (_type_, optional): densify the network section geometries to ensure network edges are not longer than this threshold. This ensures cell centres are properly snapped to interior section nodes. Defaults to None.
        duration_simplification_fun (_type_, optional): function applied to output duration indicators to simplify it. It could be a simple rounding. Defaults to None.
        keep_distance_to_node (bool, optional): Set to true to store the distance from the grid cell to the network node it is snapped to. Can be used to control snapping effect. Defaults to False.
        num_processors (int, optional): Number of processes to use, for parallel processing. Defaults to 1.
        show_detailled_messages (bool, optional): set to true to see verbode debugging messages. Defaults to False.
        shuffle (bool, optional): set to true to shuffle the tiles before processing. Keep to false to process the tiles in sequential order. Defaults to False.
    """

    # clamp bbox to fit with file_size
    clamp = lambda v : floor(v/file_size)*file_size
    [xmin,ymin,xmax,ymax] = [clamp(v) for v in bbox]

    # build list of tiles
    processes_params = cartesian_product_comp(xmin, ymin, xmax, ymax, file_size)

    # shuffle, if required
    if shuffle: random.shuffle(processes_params)

    # build list of processes parameters
    processes_params = [ (
            xy,
            extention_buffer,
            file_size,
            out_folder,
            pois_loader,
            road_network_loader,
            k,
            weight_function,
            is_not_snappable_fun,
            initial_node_level_fun,
            final_node_level_fun,
            is_start_blocked,
            is_end_blocked,
            cell_id_fun,
            grid_resolution,
            cell_network_max_distance,
            to_network_speed_ms,
            detailled,
            densification_distance,
            duration_simplification_fun,
            keep_distance_to_node,
            show_detailled_messages,
        ) for xy in processes_params ]

    # launch parallel processes
    print(datetime.now(), "launch", len(processes_params), "process(es) on", num_processors, "processor(s)")
    Pool(num_processors).starmap(accessiblity_grid_k_nearest_dijkstra, processes_params)

