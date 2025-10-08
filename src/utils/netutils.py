import math
from rtree import index
from shapely.geometry import shape

from utils.geomutils import densify_line
from collections import defaultdict


'''
def shortest_path_geometry(sp):
    coordinates_tuples = [tuple(map(float, coord.split('_'))) for coord in sp]
    return LineString(coordinates_tuples)
'''

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




def ___graph_adjacency_list_from_geodataframe(sections_iterator,
                                              weight_fun_pos = lambda feature,sl:sl,
                                              weight_fun_neg = lambda feature,sl:sl,
                                              is_not_snappable_fun = None,
                                              coord_simp=round,
                                              detailled=False,
                                              densification_distance=None,
                                              initial_node_level_fun=None,
                                              final_node_level_fun=None):
    """
    Build a directed graph from a network stored in a geo dataset.

    :param sections_iterator: fiona iterator to the dataset containing the road sections, with linear geometry
    :param weight_fun: function returning a segment weight, based on the feature and the segment length
    :param direction_fun: return section direction ('both', 'oneway', 'forward', 'backward')
    :param is_not_snappable_fun: return if the nodes of a section are not snappable.
    :param coord_simp: a function used to build node id from node coordinates.
    :param detailled: If true, all line vertices become graph nodes, otherwise only the initial and final vertices.
    :param densification_distance: If detailled=true, this will apply densification on line geometries to ensure vertices are not to far. When two consecutive coordinates are too far, vertices are inserted between them. This can be usefull for graph snapping purposes.
    :param initial_node_level_fun: For non planar graphs, a function returning the level of the line initial node.
    :param final_node_level_fun: For non planar graphs, a function returning the level of the line final node.
    :return: graph (adjacency list: {node_id: [(neighbor_node_id, travel_time)]})
    """

    graph = defaultdict(list)
    snappable_nodes = set()

    # function to build node id based on its coordinates
    def node_id(point):
        """Create a unique node id from a Point geometry."""
        return str(coord_simp(point[0])) +'_'+ str(coord_simp(point[1]))
        #return f"{point.x:.6f}_{point.y:.6f}"

    for f in sections_iterator:

        # get line coordinates
        geom = f['geometry']
        if geom['type'] != 'LineString': continue
        coords = geom['coordinates']

        # use only first and last vertices if not detailled
        if not detailled:
            coords = [ coords[0], coords[-1] ]

        # densify coordinates list
        if densification_distance is not None and densification_distance>0:
            coords = densify_line(coords, densification_distance)

        # code for initial and final node levels
        ini_node_level = "" if initial_node_level_fun == None else "_" + str(initial_node_level_fun(f))
        fin_node_level = "" if final_node_level_fun == None else "_" + str(final_node_level_fun(f))

        # get if the section is snappable
        is_snappable = True if is_not_snappable_fun==None else not is_not_snappable_fun(f)

        # make first node
        p1 = coords[0]
        n1 = node_id(p1) + ini_node_level

        nb = len(coords) - 1
        for i in range(nb):

            # make next node
            p2 = coords[i+1]
            n2 = node_id(p2)

            # add node code part for levels
            if i==nb-1: n2 += fin_node_level # for the last node, add the final node level code
            else: n2 += ini_node_level+fin_node_level # for vertex nodes, add both initial and final node codes

            # may happen
            if n1==n2: continue

            # get segment weights
            if detailled: segment_length_m = math.hypot(p1[0]-p2[0], p1[1]-p2[1])
            else: segment_length_m = shape(geom).length
            w_pos = weight_fun_pos(f, segment_length_m)
            w_neg = weight_fun_neg(f, segment_length_m)

            print(w_pos, w_neg)

            # Add directed edge(s)
            if w_pos>=0: graph[n1].append((n2, w_pos))
            elif graph[n1] is None: graph[n1] = []
            if w_neg>=0: graph[n2].append((n1, w_neg))
            elif graph[n2] is None: graph[n2] = []

            '''
            # Add directed edge(s)
            if direction == 'both':
                if w_pos>=0: graph[n1].append((n2, w_pos))
                if w_neg>=0: graph[n2].append((n1, w_neg))
            # (assume 'oneway' means forward)
            if direction == 'forward' or  direction == 'oneway':
                if w_pos>=0: graph[n1].append((n2, w_pos))
                if graph[n2] is None: graph[n2] = []
            if direction == 'backward':
                if graph[n1] is None: graph[n1] = []
                if w_neg>=0: graph[n2].append((n1, w_neg))
            '''

            # collect snappable nodes
            if is_snappable: snappable_nodes.update([n1, n2])

            # next segment
            p1 = p2
            n1 = n2

    return { 'graph':graph, 'snappable_nodes':list(snappable_nodes) }





def nodes_spatial_index(graph):
    nodes = []
    for node in graph.nodes(): nodes.append(node)

    if graph.number_of_nodes() == 0: return index.Index()

    # prepare list of elements to add
    items = []
    for i in range(graph.number_of_nodes()):
        node = nodes[i]
        [x,y] = node_coordinate(node)
        items.append((i, (x,y,x,y), None))

    # build index
    idx = index.Index(((i, box, obj) for i, box, obj in items))
    return idx



def nodes_spatial_index_adjacendy_list(nodes):
    if not nodes:
        return index.Index()

    # build index
    idx = index.Index(
        ( (i, (x, y, x, y), None) for i, node in enumerate(nodes)
          for x, y in [node_coordinate(node)] )
    )
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



