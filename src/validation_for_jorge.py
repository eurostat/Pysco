import geopandas as gpd
from rtree import index
from shapely.geometry import Point, LineString
from shapely.ops import polygonize, unary_union, nearest_points






def validate(gpkg_path, output_gpkg, epsilon = 0.001, bbox=None, detect_microscopic_segments=True, detect_noding=True, check_polygonisation=True, check_sf_validity=True):
    # list of issues
    issues = []

    print("load features")
    gdf = gpd.read_file(gpkg_path, bbox=bbox)

    if check_sf_validity:
        print("get feature geometries")
        mps = gdf["geometry"].geometry.tolist()
        print(len(mps), "features")

        for g in mps:
            v = g.is_valid
            if not v: print("Non valid geometry around: ", g.centroid)
            # in addition, check effect of the buffer_0.
            # Buffer_0 operation cleans geometries. It removes duplicate vertices.
            g_ = g.buffer(0)
            if count_vertices(g) != count_vertices(g_):
                print("Issue for geometry around: ", g.centroid)
        del mps

    # convert to line geometries
    gdf = gdf.explode(index_parts=True)
    print(len(gdf), "polygons")


    if True:
        print("decompose multi polygons to simple polygons")
        polys = gdf.explode(index_parts=False)["geometry"]
        polys = gdf.geometry.tolist()

        print('make spatial index')
        items = []
        for i in range(len(polys)):
            g = polys[i]
            items.append((i, g.bounds, None))
        idx = index.Index(((i, box, obj) for i, box, obj in items))
        del items

        print("check intersection")
        for i in range(len(polys)):
            g = polys[i]
            intersl = list(idx.intersection(g.bounds))
            for j in intersl:
                if i<=j: continue
                gj = polys[j]
                inte = g.intersects(gj)
                if not inte: continue
                inte = g.intersection(gj)
                if inte.area == 0: continue
                print("intersection around", inte.centroid, "area=", inte.area)
        del polys



    gdf = gdf.geometry.boundary
    gdf = gdf.explode(index_parts=True)
    gdf = gdf.geometry.tolist()
    print(len(gdf), "lines")


    if check_polygonisation:

        # unionise lines, to remove duplicates
        lines = unary_union(gdf)
        lines = list(lines.geoms)
        print(len(lines), "lines")

        # polygonise lines
        polygons = list(polygonize(lines))
        print(len(polygons), "polygons after polygonisation")
        del lines

        # check polygons
        for poly in polygons:
            poly_ = poly.buffer(-epsilon)
            if poly_.is_empty:
                issues.append(["Thin polygon", "thin polygon", poly.centroid])
        del polygons


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
    gdf = gdf.drop_duplicates()
    print("    without duplicates:", len(gdf))
    gdf.to_file(output_gpkg, layer="issues", driver="GPKG")





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






gf = "/home/juju/Bureau/jorge_stuff/AU_NO_SE_FI_V.gpkg"
bbox = None #(4580000, 3900000, 4599000, 3970000)
validate(gf, "/home/juju/Bureau/jorge_stuff/issues.gpkg", bbox=bbox)
#check_validity(gf)
#check_intersections(gf)
#check_polygonise(gf, bbox=bbox)

