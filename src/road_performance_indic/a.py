from shapely.geometry import box,Polygon
import geopandas as gpd
from datetime import datetime
import networkx as nx
import concurrent.futures
import fiona
import fiona.transform
from shapely.geometry import shape, mapping
from rtree import index
import csv


#from utils.featureutils import loadFeatures


population_grid = "/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg"

tomtom = "/home/juju/geodata/tomtom/tomtom_202312.gpkg"
tomtom_loader = lambda bbox: gpd.read_file('/home/juju/geodata/tomtom/2021/nw.gpkg', 'r', driver='GPKG', bbox=bbox),

output_csv = "/home/juju/gisco/road_transport_performance/indicator1.csv"

bbox = (3750000, 2720000, 3960000, 2970000)


# population straight. Load population grid. Turn into points. Make spatial index.
def process1(population_grid, layer="census2021", only_populated_cells=True, bbox=None, radius_m = 120000):

    print(datetime.now(), "Loading population grid...", population_grid)
    gpkg = fiona.open(population_grid, 'r', driver='GPKG')
    cells = list(gpkg.items(bbox=bbox,layer=layer))

    print(datetime.now(), len(cells), "cells loaded")

    print(datetime.now(), "index cells...")

    # Initialize R-tree spatial index
    spatial_index = index.Index()
    # Dictionary to store geometries
    cells_ = {}

    # make index
    for i, c in enumerate(cells):
        c = c[1]
        pop = c["properties"]["T"]
        if only_populated_cells and pop == 0: continue
        geom = shape(c["geometry"])
        pt = geom.centroid
        #print(pt)
        #geom = shape(feature["geometry"])  # Convert to Shapely geometry
        spatial_index.insert(i, geom.bounds)
        cells_[i] = {"pop":pop, "x":pt.x, "y":pt.y, "GRD_ID": c["properties"]["GRD_ID"]}

    #free memory
    del cells

    #precompute
    radius_m_s = radius_m * radius_m

    print(datetime.now(), "compute indicator for each cell...")
    output = []
    for i in cells_:
        c = cells_[i]
        x=c["x"]
        y=c["y"]

        #get close cells using spatial index
        close_cells = list(spatial_index.intersection((x-radius_m, y-radius_m, x+radius_m, y+radius_m)))

        #compute population total
        tot = 0
        for i2 in close_cells:
            c2 = cells_[i2]
            dx = x-c2["x"]
            dy = y-c2["y"]
            #too far: skip
            if dx*dx+dy*dy>radius_m_s :continue

            #sum population
            tot += c2["pop"]

        #store output data
        output.append({pop:tot,"GRD_ID":c["GRD_ID"]})

    #free memory
    del spatial_index
    del cells_

    print("Save as CSV")
    file = open(output_csv, mode="w", newline="", encoding="utf-8")
    writer = csv.DictWriter(file, fieldnames=output[0].keys())
    writer.writeheader()
    writer.writerows(output)

    print(datetime.now(), "Done.")

process1(population_grid, bbox=bbox)

