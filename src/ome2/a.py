import geopandas as gpd
from shapely.geometry import box

out_folder = '/home/juju/Bureau/gisco/OME2_analysis/'

print("loading...")
gdf = gpd.read_file(out_folder+"test.gpkg")
print(len(gdf))

#netwrok analysis libs:
#NetworkX
#igraph: C with interfaces for Python
#Graph-tool: implemented in C++ with a Python interface

