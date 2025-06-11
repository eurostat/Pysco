import numpy as np
import pandas as pd
from datetime import datetime
#import heapq
import sys
import os

from numba import njit, types
from numba.typed import List



sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.convert import parquet_grid_to_geotiff
from utils.netutils import ___graph_adjacency_list_from_geodataframe, distance_to_node, nodes_spatial_index_adjacendy_list
from utils.tomtomutils import direction_fun, final_node_level_fun, initial_node_level_fun, is_not_snappable_fun, weight_function
from utils.featureutils import iter_features
from utils.gridutils import get_cell_xy_from_id
#from utils.networkxutils import adjacency_dict_to_networkx


'''
def dijkstra_with_cutoff(g, n, destinations, cutoff):
    """
    Ultra-fast Dijkstra for adjacency matrix to get destinations within cutoff.
    Parameters:
    - g: 2D numpy array (adjacency matrix with np.inf for no edge)
    - n: source node (int)
    - cutoff: maximum cost (float)
    - destinations: list of target node indices (list of int)

    Returns:
    - List of destinations reachable within cutoff cost
    """
    num_nodes = g.shape[0]
    distances = np.full(num_nodes, np.inf)
    distances[n] = 0.0

    visited = np.zeros(num_nodes, dtype=bool)
    heap = [(0.0, n)]

    dest_set = set(destinations)
    found_destinations = []

    while heap:
        current_dist, u = heapq.heappop(heap)

        if visited[u]: continue
        visited[u] = True

        if u in dest_set:
            if current_dist <= cutoff:
                found_destinations.append(u)
            dest_set.remove(u)
            if not dest_set: break # early stop if all destinations found

        if current_dist > cutoff: continue  # no need to continue exploring this path

        neighbors = np.where(np.isfinite(g[u]))[0]
        for v in neighbors:
            if visited[v]: continue
            new_dist = current_dist + g[u, v]
            if new_dist < distances[v]:
                distances[v] = new_dist
                heapq.heappush(heap, (new_dist, v))

    return found_destinations
'''

'''
def dijkstra_with_cutoff_old(graph, origin, destinations, cutoff=None, only_nodes=False):
    """
    graph: dict of {node: list of (neighbor, weight)}
    origin: origin node
    destinations: set of destination nodes
    cutoff: maximal cost value - beyond, route is ignored
    """
    heap = [(0, origin)]
    visited = set()
    result = {}

    while heap:
        cost, node = heapq.heappop(heap)

        if node in visited: continue
        visited.add(node)

        # if destination reached, store cost
        if node in destinations:
            result[node] = cost
            # Optionnal : early exit is all destinations reached
            #if len(result) == len(destinations): break

        # Ignore if cost beyond cutoff
        if cutoff is not None and cutoff>0 and cost > cutoff: continue

        for neighbor, weight in graph.get(node, []):
            if neighbor not in visited:
                new_cost = cost + weight
                if cutoff is not None and cutoff>0 and new_cost <= cutoff:
                    heapq.heappush(heap, (new_cost, neighbor))

    if only_nodes: return result.keys()
    return result
'''


def prepare_graph_dict(graph):
    """
    Convert {node: [(neighbor, weight), ...]} into two lists:
    - neighbors: list of lists of neighbors
    - weights: list of lists of corresponding weights

    Returns:
        neighbors, weights, node_to_index, index_to_node
    """
    nodes = sorted(graph.keys())
    node_to_index = {node: i for i, node in enumerate(nodes)}
    index_to_node = {i: node for i, node in enumerate(nodes)}

    num_nodes = len(nodes)
    neighbors = [[] for _ in range(num_nodes)]
    weights = [[] for _ in range(num_nodes)]

    for node, edges in graph.items():
        i = node_to_index[node]
        for neighbor, weight in edges:
            neighbors[i].append(node_to_index[neighbor])
            weights[i].append(weight)

    return neighbors, weights, node_to_index, index_to_node



@njit
def dijkstra_with_cutoff_numba(neighbors, weights, origin, destinations, cutoff):
    num_nodes = len(neighbors)
    max_cost = np.inf
    distances = np.full(num_nodes, max_cost)
    distances[origin] = 0.0

    visited = np.zeros(num_nodes, dtype=np.bool_)
    heap = List()
    heap.append((0.0, origin))

    result_nodes = List()
    result_costs = List()

    dest_mask = np.zeros(num_nodes, dtype=np.bool_)
    for d in destinations:
        dest_mask[d] = True
    remaining_dest_count = len(destinations)

    while heap:
        heap.sort()
        cost, u = heap.pop(0)

        if visited[u]:
            continue
        visited[u] = True

        if dest_mask[u]:
            result_nodes.append(u)
            result_costs.append(cost)
            dest_mask[u] = False
            remaining_dest_count -= 1
            if remaining_dest_count == 0:
                break

        if cutoff > 0.0 and cost > cutoff:
            continue

        for i in range(len(neighbors[u])):
            v = neighbors[u][i]
            weight = weights[u][i]
            if visited[v]:
                continue
            new_cost = cost + weight
            if new_cost < distances[v] and (cutoff <= 0.0 or new_cost <= cutoff):
                distances[v] = new_cost
                heap.append((new_cost, v))

    return result_nodes, result_costs





# https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.dense.floyd_warshall.html
# computation time of dijskra: 0.7s per node -> 1h30 per 100km tile
#TODO restricts to populated cells
#TODO cutoff also based on straight distance to origin ?



# bbox
[ x_part, y_part ] = [3750000, 2720000]
partition_size = 10000
show_detailled_messages =True
grid_resolution = 1000
cell_network_max_distance = grid_resolution * 2

extention_buffer = 0 #180000 #200 km
duration_s = 60 * 10 #1h30=90min

# population grid
population_grid = "/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg"

# tomtom road network
tomtom_year = "2023"
def road_network_loader(bbox): return iter_features("/home/juju/geodata/tomtom/tomtom_"+tomtom_year+"12.gpkg", bbox=bbox)
#TODO exclude ferry links

# population grid
def population_grid_loader(bbox): return iter_features("/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg", bbox=bbox)

#def cell_id_fun(x,y): return "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))


# build partition extended bbox
extended_bbox = (x_part-extention_buffer, y_part-extention_buffer, x_part+partition_size+extention_buffer, y_part+partition_size+extention_buffer)

if show_detailled_messages: print(datetime.now(),x_part,y_part, "make graph")
roads = road_network_loader(extended_bbox)
gb_ = ___graph_adjacency_list_from_geodataframe(roads,
                                                    weight_fun = weight_function,
                                                    direction_fun = direction_fun,
                                                    is_not_snappable_fun = is_not_snappable_fun,
                                                    detailled = False,
                                                    densification_distance = grid_resolution,
                                                    initial_node_level_fun = initial_node_level_fun,
                                                    final_node_level_fun = final_node_level_fun)
graph = gb_['graph']
snappable_nodes = gb_['snappable_nodes']
del gb_, roads
if show_detailled_messages: print(datetime.now(),x_part,y_part, len(graph.keys()), "nodes,", len(snappable_nodes), "snappable nodes.")
#if(len(snappable_nodes)==0): return #TODO add that
#if(len(graph.keys())==0): return

if show_detailled_messages: print(datetime.now(),x_part,y_part, "build nodes spatial index")
idx = nodes_spatial_index_adjacendy_list(snappable_nodes)

# dictionnary that assign population to graph node
node_pop_dict = {}

# the populated cells within bbox
populated_cells = []


if show_detailled_messages: print(datetime.now(),x_part,y_part, "Project population grid on graph nodes")
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
    if x>=x_part and y>=y_part and x<x_part+partition_size and y<y_part+partition_size:
        populated_cells.append((id,x,y))
del cells

# destination nodes: all nodes with population
populated_nodes = node_pop_dict.keys()
if show_detailled_messages: print(datetime.now(),x_part,y_part, len(populated_nodes), "populated nodes")

# output data
grd_ids = [] # the cell identifiers
accessible_populations = [] # the values corresponding to the cell identifiers

# a cache structure, to ensure there is no double computation for some nodes
# it could happen, since some cells may snap to a same graph node
cache = {}

if show_detailled_messages: print(datetime.now(),x_part,y_part, "Prepare graph")
neighbors, weights, node_to_index, index_to_node = prepare_graph_dict(graph)
populated_nodes = populated_nodes.map(node_to_index)

# go through cells
if show_detailled_messages: print(datetime.now(),x_part,y_part, "compute routing for", len(populated_cells), "cells")
r2 = grid_resolution / 2

#for x in range(x_part, x_part+partition_size, grid_resolution):
#    for y in range(y_part, y_part+partition_size, grid_resolution):
for pc in populated_cells:
    id, x, y = pc

    # snap cell centre to the snappable nodes, using the spatial index
    ni_ = next(idx.nearest((x+r2, y+r2, x+r2, y+r2), 1), None)
    if ni_ == None:
        print("graph node not found for cell", x,y)
        continue
    n = snappable_nodes[ni_]

    # check if value was not already computed - try to find it in the cache
    if n in cache:
        #print(n, cache[n])
        accessible_populations.append(cache[n])
        grd_ids.append(id) #cell_id_fun(x,y))
        continue

    # compute distance from cell centre to node, and skip if too far
    dtn = distance_to_node(n, x+r2, y+r2)
    if cell_network_max_distance>0 and dtn>= cell_network_max_distance: continue

    # compute dijkstra
    print(datetime.now(), n)

    origin = node_to_index[n]
    nodes_found, costs_found = dijkstra_with_cutoff_numba(neighbors, weights, origin, populated_nodes, duration_s)
    #result = dijkstra_with_cutoff(graph, n, populated_nodes, duration_s, only_nodes=True)
    #print(len(result),"/",len(populated_nodes))

    print(nodes_found)
    break

    # sum of nodes population
    sum_pop = 0
    for nn in result:
        #if nn in node_pop_dict:
            sum_pop += node_pop_dict[nn]

    # store cell value
    accessible_populations.append(sum_pop)
    grd_ids.append(id) #cell_id_fun(x,y))

    # cache value, to be sure is is not computed another time
    cache[n] = sum_pop

print(datetime.now(), x_part, y_part, len(grd_ids), "cells created")

#return [ grd_ids, accessible_populations ]

if show_detailled_messages: print(datetime.now(), "save output")
data = { 'GRD_ID':grd_ids, 'ACC_POP_1H30':accessible_populations }
print(datetime.now(), "save as parquet")
parquet_out = "/home/juju/gisco/road_transport_performance/accessible_population.parquet"
pd.DataFrame(data).to_parquet(parquet_out)

# to gpkg
parquet_grid_to_geotiff( [parquet_out], "/home/juju/gisco/road_transport_performance/accessible_population.tiff", dtype=np.int32, compress='deflate')


if show_detailled_messages: print(datetime.now(), "done")
