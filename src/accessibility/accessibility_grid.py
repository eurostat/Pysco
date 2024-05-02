from shapely.geometry import box,Polygon
import geopandas as gpd
from datetime import datetime
import networkx as nx
import concurrent.futures

import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from utils.utils import cartesian_product_comp
from utils.netutils import graph_from_geodataframe,nodes_spatial_index,distance_to_node

def accessibility_grid(pois_loader,
                       road_network_loader,
                       weight_function,
                       bbox,
                       out_folder,
                       out_file,
                       cell_id_fun=lambda x,y:str(x)+"_"+str(y),
                       grid_resolution=1000,
                       partition_size = 100000,
                       extention_buffer = 30000,
                       detailled = False,
                       crs = 'EPSG:3035',
                       num_processors_to_use = 1):

    def proceed_partition(xy):
        [x_part,y_part] = xy

        #partition extended bbox
        extended_bbox = box(x_part-extention_buffer, y_part-extention_buffer, x_part+partition_size+extention_buffer, y_part+partition_size+extention_buffer)

        print(datetime.now(),x_part,y_part, "load POIs")
        pois = pois_loader(extended_bbox)
        print(len(pois))
        if(len(pois)==0): return

        print(datetime.now(),x_part,y_part, "load and filter network links")
        links = road_network_loader(extended_bbox)
        print(len(links), "links")
        if(len(links)==0): return

        print(datetime.now(),x_part,y_part, "make graph")
        graph = graph_from_geodataframe(links, weight_function, detailled=detailled)
        del links
        print(graph.number_of_edges(), "edges")

        print(datetime.now(),x_part,y_part, "keep larger connex component")
        connected_components = list(nx.connected_components(graph))
        largest_component = max(connected_components, key=len)
        graph = graph.subgraph(largest_component)
        print(graph.number_of_edges())

        print(datetime.now(),x_part,y_part, "get POI nodes")

        #make list of nodes
        nodes_ = []
        for node in graph.nodes(): nodes_.append(node)

        #make nodes spatial index
        idx = nodes_spatial_index(graph)

        #get POI nodes
        sources = set()
        for iii, poi in pois.iterrows():
            n = nodes_[next(idx.nearest((poi.geometry.x, poi.geometry.y, poi.geometry.x, poi.geometry.y), 1))]
            sources.add(n)
        del pois

        #TODO check pois are not too far from their node ?

        print(datetime.now(),x_part,y_part, "compute multi source dijkstra")
        duration = nx.multi_source_dijkstra_path_length(graph, sources, weight='weight')

        print(datetime.now(),x_part,y_part, "extract cell accessibility data")
        cell_geometries = [] #the cell geometries
        grd_ids = [] #the cell identifiers
        durations = [] #the durations
        distances_to_node = [] #the cell center distance to its graph node

        #go through cells
        r2 = grid_resolution / 2
        for x in range(x_part, x_part+partition_size, grid_resolution):
            for y in range(y_part, y_part+partition_size, grid_resolution):

                #get cell node
                n = nodes_[next(idx.nearest((x+r2, y+r2, x+r2, y+r2), 1))]

                #store duration, in minutes
                d = round(duration[n]/60)
                durations.append(d)

                #store distance cell center/node
                d = round(distance_to_node(n,x,y))
                distances_to_node.append(d)

                #store cell id
                grd_ids.append(cell_id_fun(x,y))

                #store grid cell geometry
                cell_geometry = Polygon([(x, y), (x+grid_resolution, y), (x+grid_resolution, y+grid_resolution), (x, y+grid_resolution)])
                cell_geometries.append(cell_geometry)

        return [cell_geometries, grd_ids, durations, distances_to_node]


    #launch parallel computation   
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_processors_to_use) as executor:
        partitions = cartesian_product_comp(bbox[0], bbox[1], bbox[2], bbox[3], partition_size)
        tasks_to_do = {executor.submit(proceed_partition, partition): partition for partition in partitions}

        #out data
        cell_geometries = []
        grd_ids = []
        durations = []
        distances_to_node = []

        # merge task outputs
        for task_output in concurrent.futures.as_completed(tasks_to_do):
            out = task_output.result()
            if(out==None): continue
            cell_geometries += out[0]
            grd_ids += out[1]
            durations += out[2]
            distances_to_node += out[3]

        print(datetime.now(), len(cell_geometries), "cells")

        print(datetime.now(), "save as GPKG")
        out = gpd.GeoDataFrame({'geometry': cell_geometries, 'GRD_ID': grd_ids, 'duration': durations, "distance_to_node": distances_to_node })
        out.crs = crs
        out.to_file(out_folder+out_file+".gpkg", driver="GPKG")

        print(datetime.now(), "save as CSV")
        out = out.drop(columns=['geometry'])
        out.to_csv(out_folder+out_file+".csv", index=False)
        print(datetime.now(), "save as parquet")
        out.to_parquet(out_folder+out_file+".parquet")
