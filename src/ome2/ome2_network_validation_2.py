import geopandas as gpd
from datetime import datetime
from netutils import node_coordinate,graph_from_geodataframe
from ome2utils import ome2_filter_road_links
from geomutils import decompose_line
from shapely import Point

folder = '/home/juju/Bureau/gisco/OME2_analysis/'
file_path = '/home/juju/Bureau/gisco/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg'
distance_threshold = 10
nb_vertices = 500
buff_dist = 1000


print(datetime.now(), "load boundaries")
bnds = gpd.read_file(folder+"bnd.gpkg")
#bnds = gpd.read_file(file_path, layer='ib_international_boundary_line')
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
out_cnts = []
out_dists = []
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
    
    print(datetime.now(), "spatial index network links")
    rn.sindex

    print(datetime.now(), "make graph")
    def edge_fun(edge,feature): edge["country"]=feature["country"]
    graph = graph_from_geodataframe(rn, edge_fun=edge_fun)

    print(datetime.now(), "get nodes with degree 1")
    nodes_1 = [node for node, degree in dict(graph.degree()).items() if degree == 1]
    #print(len(nodes_1))

    print(datetime.now(), "filter those near border")
    nodes_1 = [n for n in nodes_1 if is_close(n,bnd,distance_threshold)]
    #print(len(nodes_1))
    if(len(nodes_1)==0): continue

    print(datetime.now(), "store points", len(nodes_1))
    for n in nodes_1:
        [x,y] = node_coordinate(n)
        pt = Point(x,y)
        out_points.append(pt)

        #get node country
        #get single edge linked to the node
        edge = list(graph.edges(n))[0]
        cnt = graph.get_edge_data(*edge)["country"]
        out_cnts.append(cnt)

        #detect the network sections nearby that are in another country
        distance = None
        near = rn.sindex.intersection(pt.buffer(distance_threshold).bounds)
        for i_ in near:
            rs = rn.iloc[i_]
            #skip the ones within the same country
            if(cnt==rs["country"]): continue
            d = pt.distance(rs.geometry)
            if d>distance_threshold: continue
            if distance == None or d<distance: distance=d
        out_dists.append(distance)

print(datetime.now(), "export points as geopackage", len(out_points))
gdf = gpd.GeoDataFrame({'geometry': out_points, 'country': out_cnts, 'distance': out_dists})
gdf.crs = 'EPSG:3035'
gdf.to_file(folder+"nodes_degree_1.gpkg", driver="GPKG")



