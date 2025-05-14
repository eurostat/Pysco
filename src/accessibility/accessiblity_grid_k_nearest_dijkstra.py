import heapq
import geopandas as gpd
from shapely.geometry import LineString, Point
from collections import defaultdict




def multi_source_k_nearest_dijkstra(graph, sources, k=3, with_paths=True):
    """
    Computes the k nearest sources, their distances, and optionally paths to each node.

    :param graph: A dictionary representing the adjacency list of the graph.
    :param sources: A list of source node ids.
    :param k: Number of nearest sources to track.
    :param with_paths: Whether to track and return the paths.
    :return: A dictionary mapping each node to a sorted list of 
             {'distance': d, 'source': s, 'path': [sequence of nodes]} if with_paths,
             or {'distance': d, 'source': s} if not.
    """

    result = {node: [] for node in graph}
    priority_queue = []

    # Initialize all sources
    for source in sources:
        path = [source] if with_paths else None
        heapq.heappush(priority_queue, (0, source, source, path))  # (distance, current_node, origin_source, path)

    while priority_queue:
        current_distance, current_node, origin, path = heapq.heappop(priority_queue)

        # Check if we've already found k closest sources for this node
        current_sources = [entry['source'] for entry in result[current_node]]
        if origin in current_sources:
            continue  # Avoid duplicate source per node

        if len(result[current_node]) >= k:
            continue

        # Record this source, distance, and optional path
        entry = {
            'distance': current_distance,
            'source': origin
        }
        if with_paths:
            entry['path'] = path

        result[current_node].append(entry)

        # Visit neighbors
        for neighbor, weight in graph[current_node]:
            distance = current_distance + weight
            next_path = path + [neighbor] if with_paths else None
            heapq.heappush(priority_queue, (distance, neighbor, origin, next_path))

    # Sort lists by distance for each node
    for node in result:
        result[node].sort(key=lambda x: x['distance'])

    return result





# make graph from linear features
#TODO
#def (gdf, weight = lambda feature:feature.geometry.length, coord_simp=round, detailled=False):
def graph_adjacency_list_from_geodataframe(gdf, weight = lambda feature,sl:sl, direction_fun=lambda feature:"both"):
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






def export_dijkstra_results_to_gpkg(result, output_path, crs="EPSG:4326", k=3, with_paths=True):
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
                point_record[f'dist_{i+1}'] = entry['distance']
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
                        'distance': entry['distance'],
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



"""


# Example usage
if __name__ == "__main__":
    graph = {
        'A': [('B', 5), ('C', 10)],
        'B': [('C', 3), ('D', 9)],
        'C': [('D', 1)],
        'D': [],
        'E': [('D', 2)],
        'F': [('C', 4)]
    }

    source_nodes = ['A', 'E', 'F']
    result_without_paths = multi_source_k_nearest_dijkstra(graph, source_nodes, k=3, with_paths=True)
    for node, entries in result_without_paths.items():
        print(f"{node}:")
        for e in entries:
            print(f"  {e}")






gpkg_path = "my_network.gpkg"
layer_name = "roads"

graph = build_graph_from_gpkg(gpkg_path, layer_name, speed_attr='speed_kmh', direction_attr='direction')
print(len(graph), "nodes")


result = multi_source_k_nearest_dijkstra(graph, sources=my_sources, k=3, with_paths=True)

export_dijkstra_results_to_gpkg(
    result,
    output_path="dijkstra_results.gpkg",
    crs="EPSG:4326",
    k=3,
    with_paths=True
)

"""
