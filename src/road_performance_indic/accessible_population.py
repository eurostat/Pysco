import numpy as np
import pandas as pd
from datetime import datetime
import heapq
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.convert import parquet_grid_to_geotiff
from utils.netutils import ___graph_adjacency_list_from_geodataframe, distance_to_node, nodes_spatial_index_adjacendy_list
from utils.tomtomutils import direction_fun, final_node_level_fun, initial_node_level_fun, is_not_snappable_fun, weight_function
from utils.featureutils import iter_features
from utils.gridutils import get_cell_xy_from_id


def dijkstra_with_cutoff(graph, origin, destinations, cutoff=None, only_nodes=False):
    heap = [(0, origin)]
    dist = {origin: 0}
    result = {}

    while heap and len(result) < len(destinations):
        cost, node = heapq.heappop(heap)

        # If we already found a better path to this node, skip it
        if cost > dist.get(node, float('inf')):
            continue

        if node in destinations:
            result[node] = cost
            if len(result) == len(destinations):
                break

        if cutoff is not None and cost > cutoff:
            continue

        for neighbor, weight in graph.get(node, []):
            new_cost = cost + weight
            if cutoff is not None and new_cost > cutoff:
                continue

            if new_cost < dist.get(neighbor, float('inf')):
                dist[neighbor] = new_cost
                heapq.heappush(heap, (new_cost, neighbor))

    if only_nodes:
        return result.keys()
    return result


'''
def dijkstra_with_cutoff(graph, origin, destinations, cutoff=None, only_nodes=False):
    """
    graph: dict of {node: list of (neighbor, weight)}
    origin: origin node
    destinations: set of destination nodes
    cutoff: maximal cost value - beyond, route is ignored
    """
    heap = [(0, origin)]
    visited = set()
    result = {}

    while heap and len(result) < len(destinations):
        cost, node = heapq.heappop(heap)

        if node in visited: continue

        visited.add(node)

        if node in destinations:
            result[node] = cost
            if len(result) == len(destinations): break

        if cutoff is not None and cost > cutoff: continue

        for neighbor, weight in graph.get(node, []):
            if neighbor not in visited:
                new_cost = cost + weight
                if cutoff is None or new_cost <= cutoff:
                    heapq.heappush(heap, (new_cost, neighbor))

    if only_nodes: return result.keys()
    return result
'''


# https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.dense.floyd_warshall.html
# computation time of dijskra: 0.7s per node -> 1h30 per 100km tile
#TODO restricts to populated cells
#TODO cutoff also based on straight distance to origin ?



# bbox
[ x_part, y_part ] = [3750000, 2720000]
partition_size = 100000
show_detailled_messages =True
grid_resolution = 1000
cell_network_max_distance = grid_resolution * 2

extention_buffer = 180000 # 180000 #200 km
duration_s = 60 * 90 #1h30=90min

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

#convert to networkx graph
#if show_detailled_messages: print(datetime.now(),x_part,y_part, "convert to NetworkX graph")
#graph = adjacency_dict_to_networkx(graph)

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
        print(datetime.now(),x_part,y_part, "graph node not found for cell", x,y)
        continue
    n = snappable_nodes[ni_]

    # check if value was not already computed - try to find it in the cache
    if n in cache:
        print("Node found in cache", n, cache[n])
        accessible_populations.append(cache[n])
        grd_ids.append(id) #cell_id_fun(x,y))
        continue

    # compute distance from cell centre to node, and skip if too far
    dtn = distance_to_node(n, x+r2, y+r2)
    if cell_network_max_distance>0 and dtn>= cell_network_max_distance: continue

    # compute dijkstra
    print(n)
    result = dijkstra_with_cutoff(graph, n, populated_nodes, duration_s, only_nodes=True)
    #result = nx.single_source_dijkstra_path_length(graph, n, cutoff=duration_s, weight='weight').keys()
    #print(len(result),"/",len(populated_nodes))

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
