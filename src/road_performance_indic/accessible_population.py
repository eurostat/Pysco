from shapely.geometry import box,Polygon
import geopandas as gpd
from datetime import datetime
import networkx as nx
#import concurrent.futures
#import threading
import fiona
import fiona.transform
from shapely.geometry import shape, mapping
from rtree import index
import csv
#from utils.featureutils import loadFeatures

# bbox - set to None to compute on the entire space
bbox = (3750000, 2720000, 3960000, 2970000)


# population grid
population_grid = "/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg"

# tomtom road network
tomtom = "/home/juju/geodata/tomtom/tomtom_202312.gpkg"
tomtom_loader = lambda bbox: gpd.read_file('/home/juju/geodata/tomtom/2021/nw.gpkg', 'r', driver='GPKG', bbox=bbox),

# output CSV
accessible_population_csv = "/home/juju/gisco/road_transport_performance/accessible_population_2021.csv"


#TODO


