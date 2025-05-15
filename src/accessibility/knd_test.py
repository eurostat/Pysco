import geopandas as gpd
from shapely.geometry import box,Polygon
from accessiblity_grid_k_nearest_dijkstra import graph_adjacency_list_from_geodataframe, multi_source_k_nearest_dijkstra
from datetime import datetime
#import random

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.netutils import nodes_spatial_index_adjacendy_list, distance_to_node


k=5
with_paths = False
grid_resolution = 100

save_GPKG = True
save_CSV = False
save_parquet = False
out_folder = "/home/juju/Bureau/"
crs="EPSG:3035"
out_file = "grid"


pois_loader = lambda bbox: gpd.read_file('/home/juju/geodata/gisco/basic_services/healthcare_2023_3035.gpkg', bbox=bbox)
road_network_loader = lambda bbox: gpd.read_file('/home/juju/geodata/tomtom/tomtom_202312.gpkg', bbox=bbox)
weight_function = lambda feature, length : -1 if feature.KPH==0 else 1.1*length/feature.KPH*3.6,

cell_id_fun = lambda x,y: "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))
cell_network_max_distance = grid_resolution * 1.5

partition_size = 10000
extention_buffer = 2000
#partition_size = 100000
#extention_buffer = 50000



def proceed_partition(xy):
    [x_part,y_part] = xy


    #partition extended bbox
    extended_bbox = box(x_part-extention_buffer, y_part-extention_buffer, x_part+partition_size+extention_buffer, y_part+partition_size+extention_buffer)

    #data = gpd.read_file(tomtom, bbox=bbox)
    #print(len(data))

    print(datetime.now(),x_part,y_part, "load road sections")
    roads = road_network_loader(extended_bbox)
    print(len(roads))

    print(datetime.now(),x_part,y_part, "make graph")
    graph = graph_adjacency_list_from_geodataframe(roads)
    del roads
    print(len(graph.keys()), "nodes")

    print(datetime.now(),x_part,y_part, "load POIs")
    pois = pois_loader(extended_bbox)
    print(len(pois))

    print(datetime.now(),x_part,y_part, "get source nodes")
    idx = nodes_spatial_index_adjacendy_list(graph)
    nodes_ = list(graph.keys())
    sources = []
    for iii, poi in pois.iterrows():
        n = nodes_[next(idx.nearest((poi.geometry.x, poi.geometry.y, poi.geometry.x, poi.geometry.y), 1))]
        sources.append(n)
    del pois
    print(len(sources))

    print(datetime.now(),x_part,y_part, "compute accessiblity")
    result = multi_source_k_nearest_dijkstra(graph=graph, k=k, sources=sources, with_paths=with_paths)
    del graph

    print
    print(datetime.now(), x_part, y_part, "extract cell accessibility data")
    cell_geometries = [] #the cell geometries
    grd_ids = [] #the cell identifiers
    costs = [] #the costs - an array of arrays
    for _ in range(k): costs.append([])
    distances_to_node = [] #the cell center distance to its graph node

    #go through cells
    r2 = grid_resolution / 2
    for x in range(x_part, x_part+partition_size, grid_resolution):
        for y in range(y_part, y_part+partition_size, grid_resolution):

            #get cell node
            n = nodes_[next(idx.nearest((x+r2, y+r2, x+r2, y+r2), 1))]

            #compute distance to network and skip if too far
            dtn = round(distance_to_node(n,x+r2,y+r2))
            if cell_network_max_distance>0 and dtn>= cell_network_max_distance: continue

            #store distance cell center/node
            distances_to_node.append(dtn)

            #store costs
            cs = result[n]
            for kk in range(k): costs[kk].append(round(cs[kk]['cost']/60))

            #store cell id
            grd_ids.append(cell_id_fun(x,y))

            #store grid cell geometry
            cell_geometry = Polygon([(x, y), (x+grid_resolution, y), (x+grid_resolution, y+grid_resolution), (x, y+grid_resolution)])
            cell_geometries.append(cell_geometry)

    return [cell_geometries, grd_ids, costs, distances_to_node]




[cell_geometries, grd_ids, costs, distances_to_node] = proceed_partition([4036000, 2948000])
#proceed_partition([4000000, 2500000])

#make output geodataframe
data = {}
data['geometry'] = cell_geometries
data['GRD_ID'] = grd_ids
for kk in range(k): data['duration_'+str(kk+1)] = costs[kk]
data['distance_to_node'] = distances_to_node
out = gpd.GeoDataFrame(data)

#save output

if(save_GPKG):
    print(datetime.now(), "save as GPKG")
    out.crs = crs
    out.to_file(out_folder+out_file+".gpkg", driver="GPKG")

if(save_CSV or save_parquet): out = out.drop(columns=['geometry'])

if(save_CSV):
    print(datetime.now(), "save as CSV")
    out.to_csv(out_folder+out_file+".csv", index=False)
if(save_parquet):
    print(datetime.now(), "save as parquet")
    out.to_parquet(out_folder+out_file+".parquet")


#print(datetime.now(), "save outputs")
#export_dijkstra_results_to_gpkg(result, out_folder + "output.gpkg", crs=crs, k=k, with_paths=with_paths)

print(datetime.now(), "Done")

