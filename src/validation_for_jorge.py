import geopandas as gpd
from rtree import index
from shapely.geometry import Point, LineString
from shapely.ops import polygonize, unary_union, nearest_points

def check_validity(gpkg_path):
    print("load")
    gdf = gpd.read_file(gpkg_path)["geometry"]
    gdf = gdf.geometry.tolist()
    print(len(gdf), "geometries")

    for g in gdf:
        v = g.is_valid
        if not v: print("Non valide geometry around: ", g.centroid)
        g_ = g.buffer(0)
        nb = count_vertices(g)
        nb_ = count_vertices(g_)
        if nb != nb_: print("Issue for geometry around: ", g.centroid)




def check_intersections(gpkg_path):
    print("load")
    gdf = gpd.read_file(gpkg_path)

    print("decompose to polygons")
    gdf = gdf.explode(index_parts=False)["geometry"]
    gdf = gdf.geometry.tolist()

    print('build index')
    items = []
    for i in range(len(gdf)):
        g = gdf[i]
        items.append((i, g.bounds, None))
    idx = index.Index(((i, box, obj) for i, box, obj in items))
    del items

    print("check overlaps")
    overlaps = set()
    for i in range(len(gdf)):
        g = gdf[i]
        intersl = list(idx.intersection(g.bounds))
        for j in intersl:
            if i<=j: continue
            gj = gdf[j]
            inte = g.intersects(gj)
            if not inte: continue
            inte = g.intersection(gj).area
            if inte == 0: continue
            print("intersection",inte)


def check_polygonise(gpkg_path):

    # get polygon contours
    gdf = gpd.read_file(gpkg_path)
    gdf = gdf.explode(index_parts=True)
    print(len(gdf))
    gdf = gdf.geometry.boundary
    gdf = gdf.geometry.tolist()
    print(len(gdf), "lines")

    gdf = unary_union(gdf)
    gdf = list(gdf.geoms)
    print(len(gdf), "lines")

    polygons = list(polygonize(gdf))

    print(len(polygons), "polygons")

    for poly in polygons:
        poly_ = poly.buffer(-1)
        if poly_.is_empty:
            print("Issue around:", poly.centroid)


def count_vertices(geometry):
    if geometry.geom_type == 'Point':
        return 1
    elif geometry.geom_type == 'LineString':
        return len(geometry.coords)
    elif geometry.geom_type == 'Polygon':
        exterior_coords = list(geometry.exterior.coords)
        num_vertices = len(exterior_coords)
        # Subtract 1 because the first and last vertices of a polygon's exterior ring are the same
        return num_vertices - 1 if num_vertices > 0 else 0
    elif geometry.geom_type == 'MultiPolygon':
        num_vertices = 0
        for polygon in geometry.geoms:
            num_vertices += count_vertices(polygon)
        return num_vertices
    else:
        raise ValueError(f"Unsupported geometry type: {geometry.geom_type}")



def check_noding(gpkg_path, epsilon = 0.001, bbox=None):
    issues = []

    print("load and prepare geometries")
    gdf = gpd.read_file(gpkg_path, bbox=bbox)
    gdf = gdf.explode(index_parts=True)
    print(len(gdf), "polygons")
    gdf = gdf.geometry.boundary

    print("check coutour line types")
    for line in gdf:
        if line.geom_type == "LineString": continue
        issues.append(["Unexpected contour type " + line.geom_type, line.centroid])

    gdf = gdf.explode(index_parts=True)
    gdf = gdf.geometry.tolist()
    print(len(gdf), "lines")

    print("make list of segments and nodes")
    segments = []
    nodes = []
    for line in gdf:
        cs = list(line.coords)
        c0 = cs[0]
        nodes.append(c0)
        for i in range(1, len(cs)):
            c1 = cs[i]
            nodes.append(c1)
            segments.append( LineString([c0, c1]) )
            c0 = c1
    print(len(nodes), "nodes", len(segments), "segments")

    print("detect microscopic segments")
    for seg in segments:
        if seg.length < epsilon:
            issues.append(["Microscopic segment. length =" + str(seg.length), seg.centroid])

    print('build index of segments')
    items = []
    for i in range(len(segments)):
        s = segments[i]
        items.append((i, s.bounds, None))
    idx_seg = index.Index(((i, box, obj) for i, box, obj in items))
    del items

    print("compute node to segment analysis")
    for n in nodes:
        seg = next(idx_seg.nearest((n[0], n[1], n[0], n[1]), 1), None)
        seg = segments[seg]
        pt = Point(n)
        pos = nearest_points(pt, line)[1]
        dist = pt.distance(pos)
        print(dist)




gf = "/home/juju/Bureau/jorge_stuff/AU_NO_SE_FI_V.gpkg"
check_noding(gf)
#check_validity(gf)
#check_intersections(gf)
#check_polygonise(gf)

