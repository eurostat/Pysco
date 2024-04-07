import geopandas as gpd
from shapely.geometry import LineString,MultiPoint,Point
from datetime import datetime
from geomutils import decompose_line
import math
from netutils import shortest_path_geometry,node_coordinate,graph_from_geodataframe,a_star_euclidian_dist,a_star_speed
from ome2utils import ome2_duration
from ome2utils import ome2_filter_road_links

folder = '/home/juju/Bureau/gisco/OME2_analysis/'
file_path = '/home/juju/Bureau/gisco/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg'

cnt1 = "fr"
cnt2 = "be"

print(datetime.now(), "load nodes to get boundaries")
nodes = gpd.read_file(folder+"xborder_nodes_stamped.gpkg")
print(str(len(nodes)) + " nodes")

print(datetime.now(), "select for "+cnt1+" and "+cnt2+" only")
condition = (nodes['country_id'] == cnt1) | (nodes['country_id'] == cnt2)
nodes = nodes[condition]
print(str(len(nodes)) + " selected nodes")


window = 30000
bbox = nodes.total_bounds
rnd = lambda x: int(window*math.ceil(x/window))
bbox = [rnd(x) for x in bbox]
[xmin, ymin, xmax, ymax] = bbox
nbx = int((xmax-xmin)/window)
nby = int((ymax-ymin)/window)
print(nbx,nby, bbox)

for i in range(nbx):
    for j in range(nby):
        bbox = [xmin+i*window,ymin+j*window,xmin+(i+1)*window,ymin+(j+1)*window]
        print("******" ,bbox)

        print(datetime.now(), "load nodes")
        nodes = gpd.read_file(folder+"xborder_nodes_stamped.gpkg", bbox=bbox)
        print(len(nodes))
        if(len(nodes)==0): continue

        nodes1 = nodes[nodes['country_id'] == cnt1]
        nodes2 = nodes[nodes['country_id'] == cnt2]
        print(len(nodes1), len(nodes2))
        if(len(nodes1)==0): continue
        if(len(nodes2)==0): continue

        print(datetime.now(), "load network links")
        rn = gpd.read_file(file_path, layer='tn_road_link', bbox=bbox)
        print(len(rn))
        if(len(rn)==0): continue

        print(datetime.now(), "filter network links")
        rn = ome2_filter_road_links(rn)
        print(len(rn))
        if(len(rn)==0): continue

        print(datetime.now(), "make graph")
        graph = graph_from_geodataframe(rn, lambda f:ome2_duration(f))
        del rn
