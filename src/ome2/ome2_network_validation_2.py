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
distance_threshold = 5
nb_vertices = 500
buff_dist = 1000


print(datetime.now(), "load boundaries")
bnds = gpd.read_file(folder+"bnd.gpkg")
print(len(bnds), "boundaries")

print(datetime.now(), "decompose into small pieces")
lines = []
for g in bnds.geometry:
    lines_ = decompose_line(g, nb_vertices)
    for l in lines_: lines.append(l)
print(len(lines), "lines")

del bnds

#function to check if a network node is close to a boundary
def is_close(node, bnd, distance_threshold):
    [x,y] = node_coordinate(node)
    point = Point(x,y)
    distance = point.distance(bnd)
    return distance < distance_threshold

out_points = []
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
    #print(len(nodes_1))

    print(datetime.now(), "filter those near border")
    nodes_1 = [n for n in nodes_1 if is_close(n,bnd,distance_threshold)]
    #print(len(nodes_1))

    print(datetime.now(), "store points", len(nodes_1))
    for n in nodes_1:
        [x,y] = node_coordinate(n)
        out_points.append(Point(x,y))

print(datetime.now(), "export points as geopackage", len(out_points))
gdf = gpd.GeoDataFrame({'geometry': out_points})
gdf.crs = 'EPSG:3035'
gdf.to_file(folder+"nodes_degree_1.gpkg", driver="GPKG")


#detect pairs with different countries

