#import geopandas as gpd
from shapely.geometry import LineString, MultiPoint, Point, Polygon, MultiLineString, MultiPolygon

#function to get segments of a linestring, as 2 vertices linestrings
def extract_segments(line):
    segments = []
    coords = line.coords
    for i in range(len(coords) - 1):
        segment = LineString([coords[i], coords[i + 1]])
        segments.append(segment)
    return segments

def decompose_line(line, nb_vertices):
    lines = []
    coords = list(line.coords)
    for i in range(0, len(coords), nb_vertices):
        segment_coords = coords[i:i+nb_vertices]
        if len(segment_coords) >= 2:
            segment = LineString(segment_coords)
            lines.append(segment)
    return lines

# Define a function to decompose MultiPoints into individual Points
def decompose_point_array(geom_array):
    out = []
    for g in geom_array:
        if isinstance(g, MultiPoint):
            out.extend(g.geoms)
        else:
            out.append(g)
    return out


def average_z_coordinate(geometry):
    total_z = 0
    total_points = 0

    def process_geometry(geom):
        nonlocal total_z, total_points

        if isinstance(geom, Point):
            total_z += geom.z
            total_points += 1
        elif isinstance(geom, (LineString)):
            for point in geom.coords:
                total_z += point[2]
                total_points += 1
        elif isinstance(geom, Polygon):
            process_ring(geom.exterior)
            for interior in geom.interiors: process_ring(interior)
        elif isinstance(geom, (MultiPoint, MultiLineString, MultiPolygon)):
            for sub_geom in geom.geoms: process_geometry(sub_geom)

    def process_ring(ring):
        nonlocal total_z, total_points
        for point in ring.coords:
            total_z += point[2]
            total_points += 1

    process_geometry(geometry)

    if total_points > 0: return total_z / total_points
    return None
