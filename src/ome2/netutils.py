import networkx as nx
from shapely.geometry import LineString
import math
from rtree import index

def shortest_path_geometry(sp):
    coordinates_tuples = [tuple(map(float, coord.split('_'))) for coord in sp]
    return LineString(coordinates_tuples)

def node_coordinate(node):
    c = node.split('_')
    return [float(c[0]), float(c[1])]

def graph_from_geodataframe(gdf, weight = lambda f:f.geometry.length, coord_simp=round, edge_fun = None):
    graph = nx.Graph()
    for i, f in gdf.iterrows():
        g = f.geometry

        #create initial node
        pi = g.coords[0]
        pi = str(coord_simp(pi[0])) +'_'+ str(coord_simp(pi[1]))

        #create final node
        pf = g.coords[-1]
        pf = str(coord_simp(pf[0])) +'_'+ str(coord_simp(pf[1]))

        #compute weight
        w = weight(f)

        #add edge
        graph.add_edge(pi, pf, weight=w)

        #in case there is a need to do some stuff on the newly created edge, such as copying feature data, etc.
        if edge_fun != None: edge_fun(graph[pi][pf],f)

    return graph



def nodes_spatial_index(graph):
    nodes = []
    for node in graph.nodes(): nodes.append(node)

    idx = index.Index()
    for i in range(graph.number_of_nodes()):
        node = nodes[i]
        [x,y] = node_coordinate(node)
        idx.insert(i, (x,y,x,y))
    return idx


def a_star_euclidian_dist(n1, n2):
    [x1, y1] = node_coordinate(n1)
    [x2, y2] = node_coordinate(n2)
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

def a_star_manhattan_dist(n1, n2):
    [x1, y1] = node_coordinate(n1)
    [x2, y2] = node_coordinate(n2)
    return math.abs(x1-x2)+math.abs(y1-y2)


def a_star_speed(distance_function, speed_kmh):
    return lambda n1,n2: distance_function(n1,n2) / speed_kmh * 3.6



