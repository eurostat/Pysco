from shapely.geometry import box,Polygon
import geopandas as gpd
from datetime import datetime
import networkx as nx
import concurrent.futures
import fiona
import fiona.transform
from shapely.geometry import shape, mapping
from rtree import index


tomtom = "/home/juju/geodata/tomtom/tomtom_202312.gpkg"
population_grid = "/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg"


tomtom_loader = lambda bbox: gpd.read_file('/home/juju/geodata/tomtom/2021/nw.gpkg', bbox=bbox),


# population straight. Load population grid. Turn into points. Make spatial index.
def process1(population_grid):


    print(datetime.now(), "Loading population grid...", population_grid)
    cells = fiona.open(population_grid, layer="census2021")
    print(datetime.now(), len(cells), "cells loaded")

    print(datetime.now(), "index cells...")

    # Initialize R-tree spatial index
    spatial_index = index.Index()
    # Dictionary to store geometries
    cells_ = {}

    for i, c in enumerate(cells):
        geom = shape(c["geometry"])
        #pt = geom.centroid
        #print(pt)
        #geom = shape(feature["geometry"])  # Convert to Shapely geometry
        spatial_index.insert(i, geom.bounds)  # Insert into spatial index
        cells_[i] = c  # Store cell in a dictionary


    # Perform spatial index search
    #possible_matches = list(spatial_index.intersection(search_point.buffer(search_radius_deg).bounds))
    # Filter exact matches (since R-tree works with bounding boxes)
    #matching_points = [geometries[i] for i in possible_matches if geometries[i].distance(search_point) <= search_radius_deg]

    print(datetime.now(), "Done.")

process1(population_grid)


