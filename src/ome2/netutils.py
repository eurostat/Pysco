from shapely.geometry import LineString

def shortest_path_geometry(sp):
    coordinates_tuples = [tuple(map(float, coord.split('_'))) for coord in sp]
    return LineString(coordinates_tuples)

def node_coordinate(node):
    c = node.split('_')
    x=float(c[0]); y=float(c[1])
    return [x,y]
