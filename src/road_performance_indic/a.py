
import geopandas as gpd



tomtom = "/home/juju/geodata/tomtom/tomtom_202312.gpkg"
population_grid = "/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg"


tomtom_loader = lambda bbox: gpd.read_file('/home/juju/geodata/tomtom/2021/nw.gpkg', bbox=bbox),


# population straight. Load population grid. Turn into points. Make spatial index.
def process1(population_grid):
    print("Process", tomtom, population_grid)

    cells = gpd.read_file(population_grid),
    print(len(cells), "cells loaded")


process1(population_grid)


