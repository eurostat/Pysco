import geopandas as gpd
from shapely.geometry import LineString,MultiPoint,Point
from datetime import datetime
from geomutils import decompose_line

folder = '/home/juju/Bureau/gisco/OME2_analysis/'
file_path = '/home/juju/Bureau/gisco/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg'

print(datetime.now(), "load nodes")
gdf = gpd.read_file(folder+"xborder_nodes.gpkg")
print(str(len(gdf)) + " nodes")
