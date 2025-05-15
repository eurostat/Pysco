import geopandas as gpd
from shapely.geometry import box,Polygon
from datetime import datetime
import heapq
from shapely.geometry import LineString, Point
from collections import defaultdict

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.netutils import nodes_spatial_index_adjacendy_list, distance_to_node




def ___multi_source_k_nearest_dijkstra(graph, sources, k=3, with_paths=True):
    """
    Computes the k nearest sources, their costs, and optionally paths to each node.

    :param graph: A dictionary representing the adjacency list of the graph.
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





# make graph from linear features
#TODO
#def (gdf, weight = lambda feature:feature.geometry.length, coord_simp=round, detailled=False):
def ___graph_adjacency_list_from_geodataframe(gdf, weight = lambda feature,sl:sl, direction_fun=lambda feature:"both"):
    """
    Build a directed graph from a road network stored in a GeoPackage.

    :param gdf: geodataframe containing the road sections, with linear geometry
    :param weight: function returning a segment weight, based on the feature and the segment length
    :param direction_fun: return section direction ('both', 'oneway')
    :return: graph (adjacency list: {node_id: [(neighbor_node_id, travel_time)]})
    """
    graph = defaultdict(list)

    def node_id(point):
        """Create a unique node id from a Point geometry."""
        return f"{point.x:.6f}_{point.y:.6f}"

    for _, f in gdf.iterrows():
        geom = f.geometry
        if not isinstance(geom, LineString):
            continue  # skip invalid geometry

        coords = list(geom.coords)
        direction = direction_fun(f)

        for i in range(len(coords) - 1):
            p1 = Point(coords[i])
            p2 = Point(coords[i+1])

            segment_length_m = p1.distance(p2)
            w = weight(f, segment_length_m)

            n1 = node_id(p1)
            n2 = node_id(p2)

            # Add directed edge(s)
            if direction in ('both', 'forward'):
                graph[n1].append((n2, w))
            if direction in ('both', 'backward'):
                graph[n2].append((n1, w))

            # If one-way (assume 'oneway' means forward)
            if direction == 'oneway':
                graph[n1].append((n2, w))

    return graph






def ___export_dijkstra_results_to_gpkg(result, output_path, crs="EPSG:4326", k=3, with_paths=True):
    """
    Export the Dijkstra result to a GeoPackage: a point layer for graph nodes and (optionally) a line layer for paths.

    :param result: Result dict from multi_source_k_nearest_dijkstra()
    :param output_path: Path to output GeoPackage file
    :param crs: Coordinate Reference System (e.g. "EPSG:4326")
    :param k: Number of nearest sources stored per node
    :param with_paths: Whether the result includes paths to convert
    """
    point_records = []
    path_records = []

    for node_id, entries in result.items():
        x_str, y_str = node_id.split('_')
        x, y = float(x_str), float(y_str)
        geom = Point(x, y)

        point_record = {
            'node_id': node_id,
            'geometry': geom
        }

        for i in range(k):
            if i < len(entries):
                entry = entries[i]
                point_record[f'source_{i+1}'] = entry['source']
                point_record[f'dist_{i+1}'] = entry['cost']
                if with_paths:
                    path_str = '->'.join(entry['path'])
                    point_record[f'path_{i+1}'] = path_str

                    # Build path LineString geometry
                    path_coords = [tuple(map(float, p.split('_'))) for p in entry['path']]

                    nb = len(path_coords)
                    if(nb==1): continue
                    if(nb==0):
                        print("error")
                        continue

                    line_geom = LineString(path_coords)
                    path_records.append({
                        'from_node': entry['source'],
                        'to_node': node_id,
                        'cost': entry['cost'],
                        'geometry': line_geom
                    })
            else:
                point_record[f'source_{i+1}'] = None
                point_record[f'dist_{i+1}'] = None
                if with_paths:
                    point_record[f'path_{i+1}'] = None

        point_records.append(point_record)

    # Build GeoDataFrames
    points_gdf = gpd.GeoDataFrame(point_records, crs=crs)
    points_gdf.to_file(output_path, driver='GPKG', layer='dijkstra_nodes')

    if with_paths and path_records:
        paths_gdf = gpd.GeoDataFrame(path_records, crs=crs)
        paths_gdf.to_file(output_path, driver='GPKG', layer='dijkstra_paths')






def accessiblity_grid_k_nearest_dijkstra(pois_loader,
                       road_network_loader,
                       weight_function,
                       bbox,
                       out_folder,
                       out_file,
                       cell_id_fun=lambda x,y:str(x)+"_"+str(y),
                       grid_resolution=1000,
                       cell_network_max_distance=-1,
                       partition_size = 100000,
                       extention_buffer = 30000,
                       detailled = False,
                       crs = 'EPSG:3035',
                       num_processors_to_use = 1,
                       save_GPKG = True,
                       save_CSV = False,
                       save_parquet = False
                       ):

    #TODO
    pass




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
extention_buffer = 60000
#partition_size = 100000
#extention_buffer = 60000



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
    graph = ___graph_adjacency_list_from_geodataframe(roads)
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
    result = ___multi_source_k_nearest_dijkstra(graph=graph, k=k, sources=sources, with_paths=with_paths)
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

