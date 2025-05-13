import geopandas as gpd


tomtom = "/home/juju/geodata/tomtom/tomtom_202312.gpkg"
bbox = (4033580, 2945950, 4053279, 2958000)


data = gpd.read_file(tomtom, bbox=bbox)
print(len(data))


