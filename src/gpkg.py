import geopandas as gpd
from shapely.geometry import box

# load gpkg data using spatial index
bbox = box(minx, miny, maxx, maxy)
gdf = gpd.read_file('votre_fichier.gpkg', bbox=bbox)
