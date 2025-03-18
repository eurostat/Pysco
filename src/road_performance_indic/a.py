from shapely.geometry import box,Polygon
import geopandas as gpd
from datetime import datetime
import networkx as nx
import concurrent.futures
import fiona
import fiona.transform
from shapely.geometry import shape, mapping


tomtom = "/home/juju/geodata/tomtom/tomtom_202312.gpkg"
population_grid = "/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg"


tomtom_loader = lambda bbox: gpd.read_file('/home/juju/geodata/tomtom/2021/nw.gpkg', bbox=bbox),


# population straight. Load population grid. Turn into points. Make spatial index.
def process1(population_grid):


    print(datetime.now(), "Loading population grid...", population_grid)
    cells = fiona.open(population_grid, layer="census2021")
    print(datetime.now(), len(cells), "cells loaded")

    for c in cells:
        geom = shape(c["geometry"])
        centroid = geom.centroid
        c["geometry"] = mapping(centroid)




process1(population_grid)


