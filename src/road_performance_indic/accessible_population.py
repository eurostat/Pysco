import numpy as np
import pandas as pd
from datetime import datetime
#import heapq
import sys
import os
import graph_tool.all as gt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
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




def __parallel_process(xy,
            extention_buffer,
            partition_size,
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
            cell_id_fun = lambda x,y:str(x)+"_"+str(y)
            ):

    x_part, y_part = xy

    # build partition extended bbox
    extended_bbox = (x_part-extention_buffer, y_part-extention_buffer, x_part+partition_size+extention_buffer, y_part+partition_size+extention_buffer)

    if show_detailled_messages: print(datetime.now(),x_part,y_part, "make graph")
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
    if show_detailled_messages: print(datetime.now(),x_part,y_part, len(graph.keys()), "nodes,", len(snappable_nodes), "snappable nodes.")
    #if(len(snappable_nodes)==0): return #TODO add that
    #if(len(graph.keys())==0): return

    if show_detailled_messages: print(datetime.now(),x_part,y_part, "build graph-tool graph")
    graph, weight_prop, node_id_to_index, index_to_node_id = build_graph_tool_graph(graph)

    if show_detailled_messages: print(datetime.now(),x_part,y_part, "build nodes spatial index")
    idx = nodes_spatial_index_adjacendy_list(snappable_nodes)

    # dictionnary that assign population to graph node
    node_pop_dict = {}

    # the populated cells within bbox
    #populated_cells = []

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
        #if x>=x_part and y>=y_part and x<x_part+partition_size and y<y_part+partition_size:
        #    populated_cells.append((id,x,y))
    del cells

    # destination nodes: all nodes with population - get destination indices as a numpy array - it is faster
    populated_nodes = node_pop_dict.keys()
    #if show_detailled_messages: print(datetime.now(),x_part,y_part, "prepare populated nodes")
    #dest_indices = np.array([node_id_to_index[dest_id] for dest_id in populated_nodes if dest_id in node_id_to_index], dtype=np.int32)
    # index graph vertexes by populated node codes
    graph_id_to_vertex = {}
    for nn in populated_nodes: graph_id_to_vertex[nn] = graph.vertex(node_id_to_index[nn])


    # output data
    grd_ids = [] # the cell identifiers
    accessible_populations = [] # the values corresponding to the cell identifiers

    # a cache structure, to ensure there is no double computation for some nodes. it could happen, since some cells may snap to a same graph node
    cache = {}

    # go through cells
    if show_detailled_messages: print(datetime.now(),x_part,y_part, "compute routing")
    r2 = grid_resolution / 2
    for x in range(x_part, x_part+partition_size, grid_resolution):
        print(datetime.now(), x)
        for y in range(y_part, y_part+partition_size, grid_resolution):
        #for pc in populated_cells:
            #id, x, y = pc
            print(datetime.now(),"start")

            # snap cell centre to the snappable nodes, using the spatial index
            ni_ = next(idx.nearest((x+r2, y+r2, x+r2, y+r2), 1), None)
            if ni_ == None:
                print(datetime.now(),x_part,y_part, "graph node not found for cell", x,y)
                continue
            n = snappable_nodes[ni_]

            # check if value was not already computed - try to find it in the cache
            if n in cache:
                #print("Node found in cache", n, cache[n])
                accessible_populations.append(cache[n])
                grd_ids.append(cell_id_fun(x,y))
                continue

            # compute distance from cell centre to node, and skip if too far
            dtn = distance_to_node(n, x+r2, y+r2)
            if cell_network_max_distance is not None and cell_network_max_distance>0 and dtn>= cell_network_max_distance: continue

            # get origin node index
            origin_idx = node_id_to_index[n]

            # compute dijkstra
            print(datetime.now())
            dist_map = gt.shortest_distance(graph, source=graph.vertex(origin_idx), weights=weight_prop, max_dist=duration_s)
            print(datetime.now())

            '''
            # convert distance property map to numpy array
            dist_array = dist_map.a
            # mask of which destinations are reachable
            reachable_mask = dist_array[dest_indices] < float('inf') #TODO: duration_s ?
            reachable = [ index_to_node_id[nn] for nn in np.where(reachable_mask)[0] ]

            # sum of nodes population
            sum_pop = 0
            for nn in reachable:
                if nn in node_pop_dict:
                    sum_pop += node_pop_dict[nn]
            # check if origin node is among the reachable node
            if n not in reachable and n in node_pop_dict: sum_pop += node_pop_dict[n]
            '''

            #print(dist_map)
            #exit()

            sum_pop = 0
            inf = float('inf')
            for nn in populated_nodes:
                dist = dist_map[graph_id_to_vertex[nn]]
                if dist < inf:
                    #TODO check node is in list
                    #if nn == n: print("ok", dist)
                    sum_pop += node_pop_dict[nn]

            print(sum_pop)

            dist_map_np = np.array(dist_map)
            node_pop_np = np.array([node_pop_dict[nn] for nn in populated_nodes])
            vertex_ids_np = np.array([graph_id_to_vertex[nn] for nn in populated_nodes])

            mask = dist_map_np[vertex_ids_np] < np.inf
            sum_pop = np.sum(node_pop_np[mask])

            print(sum_pop)

            # store cell value
            accessible_populations.append(sum_pop)
            grd_ids.append(cell_id_fun(x,y))

            # cache value, to be sure is is not computed another time
            cache[n] = sum_pop
            print(datetime.now(),"end")

    print(datetime.now(), x_part, y_part, len(grd_ids), "cells created")

    return [ grd_ids, accessible_populations ]


#TODO improve efficiency
#TODO test 100m
#TODO (restricts to populated cells)
#TODO compute population <1H30 AND < 120km


# bbox
xy = [3700000, 2500000]
partition_size = 100000
show_detailled_messages =True
grid_resolution = 1000
cell_network_max_distance = grid_resolution * 2

extention_buffer = 0 # 180000 #200 km
duration_s = 60 * 90 #1h30=90min

# population grid
population_grid = "/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg"

# tomtom road network
tomtom_year = "2023"
def road_network_loader(bbox): return iter_features("/home/juju/geodata/tomtom/tomtom_"+tomtom_year+"12.gpkg", bbox=bbox)
#TODO exclude ferry links

# population grid
def population_grid_loader(bbox): return iter_features("/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg", bbox=bbox)

def cell_id_fun(x,y): return "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))

[ grd_ids, accessible_populations ] = __parallel_process(xy,
            extention_buffer,
            partition_size,
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
            show_detailled_messages = True,
            cell_id_fun = cell_id_fun,
            )


print(datetime.now(), "save output")
data = { 'GRD_ID':grd_ids, 'ACC_POP_1H30':accessible_populations }
parquet_out = "/home/juju/gisco/road_transport_performance/accessible_population.parquet"
pd.DataFrame(data).to_parquet(parquet_out)
parquet_grid_to_geotiff( [parquet_out], "/home/juju/gisco/road_transport_performance/accessible_population.tiff", dtype=np.int32, compress='deflate')
