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


#go through partitions

#load border geometry

#load network

#make network

#get nodes with degree 1 close to border

#store

#detect pairs with different countries

