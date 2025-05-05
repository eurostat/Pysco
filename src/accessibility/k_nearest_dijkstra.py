import heapq

def multi_source_k_nearest_dijkstra(graph, sources, k=3):
    """
    Computes the k nearest sources and their distances to each node.

    :param graph: A dictionary representing the adjacency list of the graph.
    :param sources: A list of source node ids.
    :param k: Number of nearest sources to track.
    :return: A dictionary mapping each node to a sorted list of (distance, source_id)
    """
    result = {node: [] for node in graph}
    priority_queue = []

    # Initialize all sources
    for source in sources:
        heapq.heappush(priority_queue, (0, source, source))  # (distance, current_node, origin_source)

    while priority_queue:
        current_distance, current_node, origin = heapq.heappop(priority_queue)

        # Check if we've already found k closest sources for this node
        current_sources = [src for _, src in result[current_node]]
        if origin in current_sources:
            continue  # Don't add duplicate source to the same node

        if len(result[current_node]) >= k:
            continue

        # Record this source and distance
        heapq.heappush(result[current_node], (current_distance, origin))

        # Visit neighbors
        for neighbor, weight in graph[current_node]:
            distance = current_distance + weight
            heapq.heappush(priority_queue, (distance, neighbor, origin))

    # Sort lists by distance for each node
    for node in result:
        result[node].sort()

    return result




def multi_source_k_nearest_dijkstra_with_paths(graph, sources, k=3):
    """
    Computes the k nearest sources, their distances, and paths to each node.

    :param graph: A dictionary representing the adjacency list of the graph.
    :param sources: A list of source node ids.
    :param k: Number of nearest sources to track.
    :return: A dictionary mapping each node to a sorted list of 
             {'distance': d, 'source': s, 'path': [sequence of nodes]}
    """
    result = {node: [] for node in graph}
    priority_queue = []

    # Initialize all sources
    for source in sources:
        heapq.heappush(priority_queue, (0, source, source, [source]))  # (distance, current_node, origin_source, path)

    while priority_queue:
        current_distance, current_node, origin, path = heapq.heappop(priority_queue)

        # Check if we've already found k closest sources for this node
        current_sources = [entry['source'] for entry in result[current_node]]
        if origin in current_sources:
            continue  # Avoid duplicate source per node

        if len(result[current_node]) >= k:
            continue

        # Record this source, distance, and path
        result[current_node].append({
            'distance': current_distance,
            'source': origin,
            'path': path
        })

        # Visit neighbors
        for neighbor, weight in graph[current_node]:
            distance = current_distance + weight
            heapq.heappush(priority_queue, (distance, neighbor, origin, path + [neighbor]))

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
    print("********** multi_source_k_nearest_dijkstra")
    k_nearest_result = multi_source_k_nearest_dijkstra(graph, source_nodes, k=2)

    for node, nearest_sources in k_nearest_result.items():
        print(f"Node {node}: {nearest_sources}")



    source_nodes = ['A', 'E', 'F']
    print("********** multi_source_k_nearest_dijkstra_with_paths")
    k_nearest_result = multi_source_k_nearest_dijkstra_with_paths(graph, source_nodes, k=2)

    for node, nearest_sources in k_nearest_result.items():
        print(f"Node {node}:")
        for entry in nearest_sources:
            print(f"  From {entry['source']}: distance = {entry['distance']}, path = {entry['path']}")














