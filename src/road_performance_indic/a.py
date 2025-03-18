
import geopandas as gpd



tomtom = "/home/juju/geodata/tomtom/tomtom_202312.gpkg"
population_grid = "/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg"


tomtom_loader = lambda bbox: gpd.read_file('/home/juju/geodata/tomtom/2021/nw.gpkg', bbox=bbox),



def process(tomtom, population_grid):
    print("Process", tomtom, population_grid)


process(tomtom, population_grid)



