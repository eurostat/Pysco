import heapq
#from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
#from collections import defaultdict



def dijkstra_with_cutoff(graph, origin, destinations, cutoff):
    """
    graph: dict de {node: list of (neighbor, weight)}
    origin: noeud de départ
    destinations: set des noeuds destinations
    cutoff: valeur maximale de coût au-delà de laquelle on ignore le chemin
    """
    costs = {}
    heap = [(0, origin)]
    visited = set()
    result = {}

    while heap:
        cost, node = heapq.heappop(heap)

        if node in visited:
            continue
        visited.add(node)

        # Si destination atteinte, enregistrer le coût
        if node in destinations:
            result[node] = cost
            # Optionnel : early exit si toutes les destinations atteintes
            if len(result) == len(destinations):
                break

        # Ignorer si le coût dépasse le cutoff
        if cost > cutoff:
            continue

        for neighbor, weight in graph.get(node, []):
            if neighbor not in visited:
                new_cost = cost + weight
                if new_cost <= cutoff:
                    heapq.heappush(heap, (new_cost, neighbor))

    return result


def compute_od_matrix(graph, origins, destinations, cutoff):
    """
    Calcule la matrice origine/destination des coûts minimaux
    """
    od_matrix = {}

    destinations_set = set(destinations)

    for origin in origins:
        costs = dijkstra_with_cutoff(graph, origin, destinations_set, cutoff)
        od_matrix[origin] = costs

    return od_matrix


'''
# Exemple d'utilisation

# Graphe sous forme d'adjacence pondérée
graph = {
    'A': [('B', 2), ('C', 5)],
    'B': [('C', 1), ('D', 3)],
    'C': [('D', 2)],
    'D': []
}

origins = ['A', 'B']
destinations = ['C', 'D']
cutoff = 4

matrix = compute_od_matrix(graph, origins, destinations, cutoff)

for origin in matrix:
    for dest in destinations:
        cost = matrix[origin].get(dest, "infini")
        print(f"De {origin} à {dest} : {cost}")
'''





'''
def compute_od_matrix_parallel(graph, origins, destinations, cutoff, max_workers=4):
    od_matrix = {}
    destinations_set = set(destinations)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(dijkstra_with_cutoff, graph, origin, destinations_set, cutoff): origin
            for origin in origins
        }

        for future in as_completed(futures):
            origin, costs = future.result()
            od_matrix[origin] = costs

    return od_matrix
'''

'''
def compute_od_matrix_multiprocessing(graph, origins, destinations, cutoff, max_workers=4):
    od_matrix = {}
    destinations_set = set(destinations)

    # Préparer les paramètres communs sous forme sérialisable pour multiprocessing
    params = [(graph, origin, destinations_set, cutoff) for origin in origins]

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(dijkstra_with_cutoff, *param): param[1]
            for param in params
        }

        for future in as_completed(futures):
            origin, costs = future.result()
            od_matrix[origin] = costs

    return od_matrix
'''




















def dijkstra_restricted_nodes(graph, sources, destinations, cutoff):
    # Initialize the distance dictionary with infinity
    distances = {node: float('inf') for node in graph}
    # Priority queue to select the node with the smallest current distance
    priority_queue = []
    
    # Dictionary to store the results for source-destination pairs
    results = {source: {dest: float('inf') for dest in destinations} for source in sources}
    
    for source in sources:
        # Reset distances for each new source
        distances = {node: float('inf') for node in graph}
        distances[source] = 0
        heapq.heappush(priority_queue, (0, source))

        while priority_queue:
            current_distance, current_node = heapq.heappop(priority_queue)

            # Stop if the current distance exceeds the cutoff
            if current_distance > cutoff:
                break

            # Explore neighbors
            for neighbor, weight in graph[current_node].items():
                distance = current_distance + weight

                # Only consider this new path if it's better
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    heapq.heappush(priority_queue, (distance, neighbor))

        # Store the results for the current source
        for dest in destinations:
            if distances[dest] <= cutoff:
                results[source][dest] = distances[dest]

    return results

'''
# Example usage:
graph = {
    'A': {'B': 1, 'C': 4},
    'B': {'C': 2, 'D': 5},
    'C': {'D': 1},
    'D': {}
}
sources = ['A', 'B']
destinations = ['C', 'D']
cutoff = 5

# Calculate the restricted distance matrix
distance_matrix = dijkstra_restricted_nodes(graph, sources, destinations, cutoff)
distance_matrix
'''