import geopandas as gpd
from shapely.geometry import LineString, Point, MultiPoint

#function to get segments of a linestring, as 2 vertices linestrings
def extract_segments(line):
    segments = []
    coords = line.coords
    for i in range(len(coords) - 1):
        segment = LineString([coords[i], coords[i + 1]])
        segments.append(segment)
    return segments

def decompose_line(line, nb_vertices):
    segments = []
    coords = list(line.coords)
    for i in range(0, len(coords), nb_vertices):
        segment_coords = coords[i:i+nb_vertices]
        if len(segment_coords) >= 2:
            segment = LineString(segment_coords)
            segments.append(segment)
    return segments

# Define a function to decompose MultiPoints into individual Points
def decompose_multipoints(multipoint):
    if isinstance(multipoint, MultiPoint):
        return [Point(xy) for xy in multipoint.coords]
    else:
        return [multipoint]

# Define a function to decompose MultiPoints into individual Points
def decompose_point_array(geometries_array):
    individual_points = [point for geometry in geometries_array for point in decompose_multipoints(geometry)]
    return individual_points
