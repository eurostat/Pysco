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

def distance_to_node(node, x, y):
    [xn,yn] = node_coordinate(node)
    return math.hypot(xn-x,yn-y)

def distance(node1, node2):
    [x1,y1] = node_coordinate(node1)
    [x2,y2] = node_coordinate(node2)
    return math.hypot(x1-x2,y1-y2)

# make graph from linear features
def graph_from_geodataframe(gdf, weight = lambda feature:feature.geometry.length, coord_simp=round, edge_fun = None, detailled=False):
    graph = nx.Graph()
    for i, feature in gdf.iterrows():
        g = feature.geometry

        if(detailled):
            #make one edge for each segment of the geometry

            #create initial node
            pi = g.coords[0]
            ni = str(coord_simp(pi[0])) +'_'+ str(coord_simp(pi[1]))

            #create graph edge for each line segment
            for i in range(1, len(g.coords)):

                #create final node
                pf = g.coords[i]
                nf = str(coord_simp(pf[0])) +'_'+ str(coord_simp(pf[1]))

                if(ni!=nf):
                    #nodes are different: make edge

                    #compute weight
                    #segment_length = math.hypot(pi[0]-pf[0],pi[1]-pf[1])
                    segment_length = distance(ni,nf) #TODO be more efficient here
                    w = weight(feature, segment_length)
                    if(w<0): continue

                    #add edge
                    graph.add_edge(ni, nf, weight=w)

                    #in case there is a need to do some stuff on the newly created edge, such as copying feature data, etc.
                    if edge_fun != None: edge_fun(graph[pi][pf],feature)

                #initial point becomes final point of the next segment
                pi=pf
                ni=nf

        else:
            #make one single edge, from initial to final vertice of the geometry

            #create initial node
            pi = g.coords[0]
            pi = str(coord_simp(pi[0])) +'_'+ str(coord_simp(pi[1]))

            #create final node
            pf = g.coords[-1]
            pf = str(coord_simp(pf[0])) +'_'+ str(coord_simp(pf[1]))

            #TODO check both nodes are not the same ?

            #compute weight
            w = weight(feature, g.length)
            if(w<0): continue

            #add edge
            graph.add_edge(pi, pf, weight=w)

            #in case there is a need to do some stuff on the newly created edge, such as copying feature data, etc.
            if edge_fun != None: edge_fun(graph[pi][pf],feature)

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



