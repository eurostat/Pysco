import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from shapely.strtree import STRtree
import os

def check_no_overlaps(gpkg_path, layer=None):
    if not os.path.isfile(gpkg_path): raise FileNotFoundError(f"File not found: {gpkg_path}")

    # Load GeoPackage
    gdf = gpd.read_file(gpkg_path, layer=layer)

    # Explode MultiPolygons into individual Polygons
    gdf = gdf.explode(ignore_index=True)

    # Ensure only polygon geometries
    gdf = gdf[gdf.geometry.type == 'Polygon']

    # Build a list of geometries and their original index
    polygons = list(gdf.geometry)
    str_tree = STRtree(polygons)

    # Test each polygon against its neighbors via spatial index
    overlaps = []
    for i, poly in enumerate(polygons):
        # Query index for possible overlaps
        possible_matches = str_tree.query(poly)
        for other in possible_matches:
            if poly == other: continue
            if poly.intersects(other): overlaps.append((i, polygons.index(other)))

    if overlaps:
        print(f"Found {len(overlaps)} overlapping pairs.")
        return overlaps  # List of (index1, index2)
    else:
        print("No overlaps found.")
        return True



