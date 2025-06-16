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



def check_polygonise(gpkg_path, bbox=None):

    print("load and prepare geometries")
    gdf = gpd.read_file(gpkg_path, bbox=bbox)
    gdf = gdf.explode(index_parts=True)
    print(len(gdf), "polygons")
    gdf = gdf.geometry.boundary
    gdf = gdf.explode(index_parts=True)
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



def check_noding(gpkg_path, output_gpkg, epsilon = 0.001, bbox=None, detect_microscopic_segments=True, detect_noding=True):
    issues = []

    print("load and prepare geometries")
    gdf = gpd.read_file(gpkg_path, bbox=bbox)
    gdf = gdf.explode(index_parts=True)
    print(len(gdf), "polygons")
    gdf = gdf.geometry.boundary
    gdf = gdf.explode(index_parts=True)
    gdf = gdf.geometry.tolist()
    print(len(gdf), "lines")

    print("make list of segments and nodes")
    segments = []
    nodes = []
    for line in gdf:
        cs = list(line.coords)
        c0 = cs[0]
        nodes.append(Point(c0))
        for i in range(1, len(cs)):
            c1 = cs[i]
            nodes.append(Point(c1))
            segments.append( LineString([c0, c1]) )
            c0 = c1
    print(len(nodes), "nodes", len(segments), "segments")

    #TODO remove duplicate nodes and segments ?
    #gseries = gpd.GeoSeries(nodes)
    #nodes = gseries.drop_duplicates().tolist()
    #del gseries

    if detect_microscopic_segments:
        print("detect microscopic segments")
        for seg in segments:
            if seg.length < epsilon:
                issues.append(["Microscopic segment. length =" + str(seg.length), "micro_segment", seg.centroid])

    if detect_noding:
        print('build index of nodes')
        items = []
        for i in range(len(nodes)):
            items.append((i, nodes[i].bounds, None))
        idx = index.Index(((i, box, obj) for i, box, obj in items))
        del items

        print("compute node to segment analysis")
        for seg in segments:
            candidate_nodes = idx.intersection(seg.bounds)
            #print(len(candidate_nodes))
            for cn in candidate_nodes:
                cn = nodes[cn]
                pos = nearest_points(cn, seg)[1]
                dist = cn.distance(pos)
                if dist == 0: continue
                if dist > epsilon: continue
                #print(cn, dist)
                issues.append(["Noding issue. dist =" + str(dist), "noding", cn])

    print("save issues as gpkg", len(issues))
    gdf = gpd.GeoDataFrame(issues, columns=["description", "type", "geometry"], crs="EPSG:3035" )
    #gdf = gdf.drop_duplicates()
    #print("    without duplicates:", len(gdf))
    gdf.to_file(output_gpkg, layer="issues", driver="GPKG")



gf = "/home/juju/Bureau/jorge_stuff/AU_NO_SE_FI_V.gpkg"
bbox = None #(4580000, 3900000, 4599000, 3970000)
check_noding(gf, "/home/juju/Bureau/jorge_stuff/issues.gpkg", bbox=bbox)
#check_validity(gf)
#check_intersections(gf)
#check_polygonise(gf, bbox=bbox)

