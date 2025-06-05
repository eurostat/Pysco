import pandas as pd
from datetime import datetime
import heapq
from shapely.geometry import shape
from collections import defaultdict
from multiprocessing import Pool
import math

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.utils import cartesian_product_comp
from utils.netutils import nodes_spatial_index_adjacendy_list, distance_to_node
from utils.geomutils import densify_line


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
        if origin in current_sources:
            continue  # Avoid duplicate source per node

        if len(result[current_node]) >= k:
            continue

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



def ___graph_adjacency_list_from_geodataframe(sections_iterator,
                                              weight_fun = lambda feature,sl:sl,
                                              direction_fun=lambda feature:"both",
                                              is_not_snappable_fun = None,
                                              coord_simp=round,
                                              detailled=False,
                                              densification_distance=None,
                                              initial_node_level_fun=None,
                                              final_node_level_fun=None):
    """
    Build a directed graph from a network stored in a geo dataset.

    :param sections_iterator: fiona iterator to the dataset containing the road sections, with linear geometry
    :param weight_fun: function returning a segment weight, based on the feature and the segment length
    :param direction_fun: return section direction ('both', 'oneway', 'forward', 'backward')
    :param is_not_snappable_fun: return if the nodes of a section are not snappable.
    :param coord_simp: a function used to build node id from node coordinates.
    :param detailled: If true, all line vertices become graph nodes, otherwise only the initial and final vertices.
    :param densification_distance: If detailled=true, this will apply densification on line geometries to ensure vertices are not to far. When two consecutive coordinates are too far, vertices are inserted between them. This can be usefull for graph snapping purposes.
    :param initial_node_level_fun: For non planar graphs, a function returning the level of the line initial node.
    :param final_node_level_fun: For non planar graphs, a function returning the level of the line final node.
    :return: graph (adjacency list: {node_id: [(neighbor_node_id, travel_time)]})
    """

    graph = defaultdict(list)
    snappable_nodes = set()

    # function to build node id based on its coordinates
    def node_id(point):
        """Create a unique node id from a Point geometry."""
        return str(coord_simp(point[0])) +'_'+ str(coord_simp(point[1]))
        #return f"{point.x:.6f}_{point.y:.6f}"

    for f in sections_iterator:

        # get driving direction
        direction = direction_fun(f)
        if direction == None: continue

        # get line coordinates
        geom = f['geometry']
        if geom['type'] != 'LineString': continue
        coords = geom['coordinates']

        # use only first and last vertices if not detailled
        if not detailled:
            coords = [ coords[0], coords[-1] ]

        # densify coordinates list
        if densification_distance is not None and densification_distance>0:
            coords = densify_line(coords, densification_distance)

        # code for initial and final node levels
        ini_node_level = "" if initial_node_level_fun == None else "_" + str(initial_node_level_fun(f))
        fin_node_level = "" if final_node_level_fun == None else "_" + str(final_node_level_fun(f))

        # get if the section is snappable
        is_snappable = True if is_not_snappable_fun==None else not is_not_snappable_fun(f)

        # make first node
        p1 = coords[0]
        n1 = node_id(p1) + ini_node_level

        nb = len(coords) - 1
        for i in range(nb):

            # make next node
            p2 = coords[i+1]
            n2 = node_id(p2)

            # add node code part for levels
            if i==nb-1: n2 += fin_node_level # for the last node, add the final node level code
            else: n2 += ini_node_level+fin_node_level # for vertex nodes, add both initial and final node codes

            # may happen
            if n1==n2: continue

            # get segment weight
            segment_length_m = math.hypot(p1[0]-p2[0], p1[1]-p2[1])
            w = weight_fun(f, segment_length_m)
            if w<0: continue

            # Add directed edge(s)
            if direction == 'both':
                graph[n1].append((n2, w))
                graph[n2].append((n1, w))
            # (assume 'oneway' means forward)
            if direction == 'forward' or  direction == 'oneway':
                graph[n1].append((n2, w))
                if graph[n2] is None: graph[n2] = []
            if direction == 'backward':
                if graph[n1] is None: graph[n1] = []
                graph[n2].append((n1, w))

            # collect snappable nodes
            if is_snappable: snappable_nodes.update([n1, n2])

            # next segment
            p1 = p2
            n1 = n2

    return { 'graph':graph, 'snappable_nodes':list(snappable_nodes) }



# function to launch in parallel for each partition
def __parallel_process(xy,
            extention_buffer,
            partition_size,
            pois_loader,
            road_network_loader,
            k,
            weight_function,
            direction_fun,
            is_not_snappable_fun,
            initial_node_level_fun,
            final_node_level_fun,
            cell_id_fun,
            grid_resolution,
            cell_network_max_distance,
            detailled,
            densification_distance,
            keep_distance_to_node):

    # get partition position
    [ x_part, y_part ] = xy

    # build partition extended bbox
    extended_bbox = (x_part-extention_buffer, y_part-extention_buffer, x_part+partition_size+extention_buffer, y_part+partition_size+extention_buffer)

    print(datetime.now(),x_part,y_part, "get POIs")
    pois = pois_loader(extended_bbox)
    if not pois: return

    print(datetime.now(),x_part,y_part, "make graph")
    roads = road_network_loader(extended_bbox)
    gb_ = ___graph_adjacency_list_from_geodataframe(roads,
                                                        weight_fun = weight_function,
                                                        direction_fun = direction_fun,
                                                        is_not_snappable_fun = is_not_snappable_fun,
                                                        detailled = detailled,
                                                        densification_distance=densification_distance,
                                                        initial_node_level_fun = initial_node_level_fun,
                                                        final_node_level_fun = final_node_level_fun)
    graph = gb_['graph']
    snappable_nodes = gb_['snappable_nodes']
    del gb_, roads
    print(datetime.now(),x_part,y_part, len(graph.keys()), "nodes,", len(snappable_nodes), "snappable nodes.")
    if(len(graph.keys())==0): return
    if(len(snappable_nodes)==0): return

    print(datetime.now(),x_part,y_part, "build nodes spatial index")
    # for snappable nodes only
    idx = nodes_spatial_index_adjacendy_list(snappable_nodes)

    print(datetime.now(),x_part,y_part, "get source nodes")
    sources = []
    for poi in pois:
        x, y = poi['geometry']['coordinates']
        n = snappable_nodes[next(idx.nearest((x, y, x, y), 1))]
        sources.append(n)
    del pois
    print(datetime.now(),x_part,y_part, len(sources), "source nodes found")
    if(len(sources)==0): return

    print(datetime.now(),x_part,y_part, "compute accessiblity")
    result = ___multi_source_k_nearest_dijkstra(graph=graph, k=k, sources=sources, with_paths=False)
    del graph, sources

    print(datetime.now(), x_part, y_part, "extract cell accessibility data")
    grd_ids = [] #the cell identifiers
    costs = [] #the costs - an array of arrays
    for _ in range(k): costs.append([])
    distances_to_node = [] #the cell center distance to its graph node

    # go through cells
    r2 = grid_resolution / 2
    for x in range(x_part, x_part+partition_size, grid_resolution):
        for y in range(y_part, y_part+partition_size, grid_resolution):

            # snap cell centre to the snappable nodes, using the spatial index
            ni_ = next(idx.nearest((x+r2, y+r2, x+r2, y+r2), 1), None)
            if ni_ == None: continue
            n = snappable_nodes[ni_]

            # compute distance from cell centre to node, and skip if too far
            dtn = distance_to_node(n, x+r2, y+r2)
            if cell_network_max_distance>0 and dtn>= cell_network_max_distance: continue

            # get costs
            cs = result[n]

            # store costs
            for kk in range(k):
                if kk>=len(cs): costs[kk].append(-1)
                else: costs[kk].append(cs[kk]['cost'])

            # store distance cell center/node
            if keep_distance_to_node:
                distances_to_node.append( round(dtn) )

            # store cell id
            grd_ids.append(cell_id_fun(x,y))

    print(datetime.now(), x_part, y_part, len(grd_ids), "cells created")

    del result, idx, snappable_nodes

    if keep_distance_to_node:
        return [grd_ids, costs, distances_to_node]
    else:
        return [grd_ids, costs]






def accessiblity_grid_k_nearest_dijkstra(pois_loader,
                       road_network_loader,
                       bbox,
                       out_parquet_file,
                       k = 3,
                       weight_function = lambda feature,sl:sl,
                       direction_fun=lambda feature:"both", #('both', 'oneway', 'forward', 'backward')
                       is_not_snappable_fun = None,
                       initial_node_level_fun=None,
                       final_node_level_fun=None,
                       cell_id_fun=lambda x,y:str(x)+"_"+str(y),
                       grid_resolution=1000,
                       cell_network_max_distance=-1,
                       partition_size = 100000,
                       extention_buffer = 30000,
                       detailled = False,
                       densification_distance = None,
                       duration_simplification_fun = None,
                       keep_distance_to_node = False,
                       num_processors_to_use = 1,
                       ):

    #launch parallel computation   
    processes_params = cartesian_product_comp(bbox[0], bbox[1], bbox[2], bbox[3], partition_size)
    processes_params = [
        (
            xy,
            extention_buffer,
            partition_size,
            pois_loader,
            road_network_loader,
            k,
            weight_function,
            direction_fun,
            is_not_snappable_fun,
            initial_node_level_fun,
            final_node_level_fun,
            cell_id_fun,
            grid_resolution,
            cell_network_max_distance,
            detailled,
            densification_distance,
            keep_distance_to_node,
        )
        for xy in processes_params
        ]

    print(datetime.now(), "launch", len(processes_params), "processes on", num_processors_to_use, "processor(s)")
    outputs = Pool(num_processors_to_use).starmap(__parallel_process, processes_params)

    print(datetime.now(), "combine", len(outputs), "outputs")
    grd_ids = []
    costs = []
    for _ in range(k): costs.append([])
    distances_to_node = []

    for out in outputs:
        # skip if empty result
        if out==None : continue
        if len(out[0])==0: continue

        # combine results
        grd_ids += out[0]
        costs_ = out[1]
        for kk in range(k): costs[kk] += costs_[kk]
        if keep_distance_to_node: distances_to_node += out[2]

    print(datetime.now(), len(grd_ids), "cells")

    #if len(cell_geometries) == 0: return

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

    # make dataframe
    out = pd.DataFrame(data)

    # save output
    print(datetime.now(), "save as parquet")
    out.to_parquet(out_parquet_file)

