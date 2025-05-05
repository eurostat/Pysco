import heapq

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


