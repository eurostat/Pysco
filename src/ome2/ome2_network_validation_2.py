import geopandas as gpd
from datetime import datetime
import math
from netutils import node_coordinate,shortest_path_geometry,graph_from_geodataframe,nodes_spatial_index,a_star_euclidian_dist
from ome2utils import ome2_filter_road_links
import networkx as nx
from geomutils import decompose_line
from shapely import Point

folder = '/home/juju/Bureau/gisco/OME2_analysis/'
file_path = '/home/juju/Bureau/gisco/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg'
distance_threshold = 10
nb_vertices = 500
buff_dist = 1000


print(datetime.now(), "load boundaries to get bounds")
bnds = gpd.read_file(folder+"bnd.gpkg")
print(len(bnds), "boundaries")

lines = []
for g in bnds.geometry:
    lines_ = decompose_line(g, nb_vertices)
    for l in lines_: lines.append(l)
del bnds
print(len(lines), "lines")

#function to check if a network node is close to a boundary
def is_close(node, bnd, distance_threshold):
    [x,y] = node_coordinate(node)
    point = Point(x,y)
    distance = point.distance(bnd)
    return distance < distance_threshold

for bnd in lines:
    bbox = bnd.bounds
    bbox = (bbox[0] - buff_dist, bbox[1] - buff_dist, bbox[2] + buff_dist, bbox[3] + buff_dist)

    print(datetime.now(), "load and filter network links")
    rn = gpd.read_file(file_path, layer='tn_road_link', bbox=bbox)
    #print(len(rn))
    if(len(rn)==0): continue
    #rn = ome2_filter_road_links(rn)
    #print(len(rn))
    #if(len(rn)==0): return

    print(datetime.now(), "make graph")
    graph = graph_from_geodataframe(rn)
    del rn

    print(datetime.now(), "get nodes with degree 1")
    nodes_1 = [node for node, degree in dict(graph.degree()).items() if degree == 1]
    print(len(nodes_1))

    print(datetime.now(), "filter those near border")
    nodes_1 = [n for n in nodes_1 if is_close(n,bnd,distance_threshold)]
    print(len(nodes_1))

#store

#detect pairs with different countries

