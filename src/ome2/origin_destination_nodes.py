import geopandas as gpd
from shapely.geometry import LineString
from datetime import datetime


folder = '/home/juju/Bureau/gisco/OME2_analysis/'

print(datetime.now(), "load boundaries")
gdf = gpd.read_file(folder+"bnd_5km.gpkg")
print(str(len(gdf)) + " boundaries")

#function to get segments of a linestring, as 2 vertices linestrings
def extract_segments(line):
    segments = []
    coords = line.coords
    for i in range(len(coords) - 1):
        segment = LineString([coords[i], coords[i + 1]])
        segments.append(segment)
    return segments

print(datetime.now(), "make segments")
segments = sum(gdf['geometry'].apply(extract_segments), [])
gdf = gpd.GeoDataFrame(geometry=segments)
gdf.crs = 'EPSG:3035'
print(str(len(gdf)) + " segments")

print(datetime.now(), "save segments")
gdf.to_file(folder+"bnd_segments.gpkg", driver="GPKG")

