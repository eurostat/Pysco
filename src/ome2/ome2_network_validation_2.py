import geopandas as gpd
from shapely.errors import GEOSException
from datetime import datetime
import math
from netutils import shortest_path_geometry,graph_from_geodataframe,nodes_spatial_index,a_star_euclidian_dist
from ome2utils import ome2_filter_road_links
import networkx as nx
import concurrent.futures
from utils import cartesian_product

folder = '/home/juju/Bureau/gisco/OME2_analysis/'
file_path = '/home/juju/Bureau/gisco/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg'
distance_threshold = 5000
num_processors_to_use = 4



print(datetime.now(), "load boundaries to get bounds")
bnds = gpd.read_file(folder+"bnd.gpkg")

#get bbox and partition information
window = 30000
bbox = bnds.total_bounds
rnd_function = lambda x: int(window*math.floor(x/window))
bbox = [rnd_function(x) for x in bbox]
[xmin, ymin, xmax, ymax] = bbox
nbx = math.floor((xmax-xmin)/window)
nby = math.floor((ymax-ymin)/window)
#print(nbx, nby, bbox)
window_margin = window * 0.1

#go through partitions
for i in range(nbx):
    for j in range(nby):
        bbox = [xmin+i*window-window_margin, ymin+j*window-window_margin, xmin+(i+1)*window+window_margin, ymin+(j+1)*window+ window_margin]
        print(bbox)

        #load network

#make network

#get nodes with degree 1 close to border

#store

#detect pairs with different countries

