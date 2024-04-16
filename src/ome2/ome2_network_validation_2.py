import geopandas as gpd
from datetime import datetime
from netutils import node_coordinate,graph_from_geodataframe
from ome2utils import ome2_filter_road_links
from geomutils import decompose_line
from shapely import Point

#Validation script for network edge matching.
# inputs:
# - boundaries lines, to check edge matching along, in ETRS89-LAEA projection
# - network dataset, as lines, in ETRS89-LAEA projection
# output: a dataset of points nearby potential edge matching issues

output_folder = '/home/juju/Bureau/gisco/OME2_analysis/'
OME_dataset = '/home/juju/Bureau/gisco/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg'
#the network layer to validate
layer = "tn_road_link"
#layer = "tn_railway_link"

#the threshold distance for the edge matching precision
distance_threshold_meter = 20



#parameters used for partionning
boundary_piece_max_vertice_number = 500
buffer_distance_meter = 1000

print(datetime.now(), "load boundaries")
#bnds = gpd.read_file(file_path, layer='ib_international_boundary_line')
boundaries = gpd.read_file(output_folder+"bnd.gpkg")
print(len(boundaries), "boundaries")

print(datetime.now(), "decompose boundaries into small pieces")
boundary_pieces = []
for g in boundaries.geometry:
    lines_ = decompose_line(g, boundary_piece_max_vertice_number)
    for l in lines_: boundary_pieces.append(l)
print(len(boundary_pieces), "lines")

del boundaries

#function to check if a network node is close to a boundary line
def is_close(node, boundary, distance):
    [x,y] = node_coordinate(node)
    return Point(x,y).distance(boundary) < distance

#output data
out_points = []
out_countries = []
out_distances = []

#deal with boundary pieces, one by one
for bp in boundary_pieces:
    #get bbox around
    bbox = bp.bounds
    bbox = (bbox[0] - buffer_distance_meter, bbox[1] - buffer_distance_meter, bbox[2] + buffer_distance_meter, bbox[3] + buffer_distance_meter)

    print(datetime.now(), "load and filter network links")
    links = gpd.read_file(OME_dataset, layer=layer, bbox=bbox)
    #print(len(links))
    if(len(links)==0): continue
    #rn = ome2_filter_road_links(links)
    #print(len(links))
    #if(len(links)==0): continue

    print(datetime.now(), "spatial index network links")
    links.sindex

    print(datetime.now(), "make graph")
    def edge_fun(edge,feature): edge["country"]=feature["country"]
    graph = graph_from_geodataframe(links, edge_fun=edge_fun)

    print(datetime.now(), "get nodes with degree 1")
    nodes_1 = [node for node, degree in dict(graph.degree()).items() if degree == 1]
    #print(len(nodes_1))

    print(datetime.now(), "filter those near border line")
    nodes_1 = [n for n in nodes_1 if is_close(n, bp, distance_threshold_meter)]
    #print(len(nodes_1))
    if(len(nodes_1)==0): continue

    print(datetime.now(), "store nodes", len(nodes_1))
    for n in nodes_1:
        [x,y] = node_coordinate(n)
        pt = Point(x,y)
        out_points.append(pt)

        #get node country
        #get single edge linked to the node
        edge = list(graph.edges(n))[0]
        node_country = graph.get_edge_data(*edge)["country"]
        out_countries.append(node_country)

        #detect the network links nearby that are from a different country
        distance = None
        near = links.sindex.intersection(pt.buffer(distance_threshold_meter).bounds)
        for i_ in near:
            link = links.iloc[i_]
            #skip the ones within the same country
            if(node_country == link["country"]): continue
            #compute distance from node to link
            d = pt.distance(link.geometry)
            #skip if too far
            if d>distance_threshold_meter: continue
            #keep shortest distance
            if distance == None or d<distance: distance=d
        #store shortest distance
        out_distances.append(distance)

print(datetime.now(), "save points", len(out_points))
gdf = gpd.GeoDataFrame({'geometry': out_points, 'country': out_countries, 'distance': out_distances})
gdf.crs = 'EPSG:3035'
gdf.to_file(output_folder+"nodes_degree_1_"+layer+".gpkg", driver="GPKG")


