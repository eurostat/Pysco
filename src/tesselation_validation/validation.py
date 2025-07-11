import geopandas as gpd
from rtree import index
from shapely.geometry import Point, LineString
from shapely.ops import polygonize, unary_union, nearest_points



#TODO: document and share with eurogeographics


def validate_polygonal_tesselation(gpkg_path, output_gpkg, bbox=None,
             check_ogc_validity=False,
             check_thin_parts=False,
             thin_part_threshold = 0.1,
             check_intersection=False,
             check_polygonisation=False,
             polygonation_check_distance_threshold = 0.1,
             check_microscopic_segments=False,
             microscopic_segment_threshold = 0.1,
             check_noding_issues=False,
             node_to_segment_distance_threshold = 0.1,
             ):
    """
    Detect issues on a polygonal tesselation dataset. Various validation rules are tested. The issues detected are stored into a gpkg file.

    Args:
        gpkg_path (str): the path to the input dataset to test, which should contain a polygonal tesselation.
        output_gpkg (str): the path to the output gpkg file describing the detected issues.
        bbox (bbox, optional): if the validation should focus only on a part of the dataset, here is the bounding box. Defaults to None, for the entire dataset.
        check_ogc_validity (bool, optional): Set to true to check the OGC validy of the polygons. Defaults to False.
        check_thin_parts (bool, optional): Set to true to detect too thin polygon parts, which may be due to gaps in the datasets. Defaults to False.
        thin_part_threshold (float, optional): the threshold for the thin part. Should be the dataset resolution. Defaults to 0.1.
        check_intersection (bool, optional): Set to true to check no polygons intersect. Defaults to False.
        check_polygonisation (bool, optional): Set to true to check no gaps exist between polygons. Defaults to False.
        polygonation_check_distance_threshold (float, optional): the threshold for the polygon gaps. Should be the dataset resolution. Defaults to 0.1.
        check_microscopic_segments (bool, optional): Set to true to check polygons with microscopic segments. Defaults to False.
        microscopic_segment_threshold (float, optional): the threshold length for what is considered as a microscopic segment. Should be the dataset resolution. Defaults to 0.1.
        check_noding_issues (bool, optional): Set to true to detect noding issues. A noding issue occurs when a polygon vertex is close to the segment of another polygon but not exactly snapped. This should result in a polygon overlap or gap between them. Defaults to False.
        node_to_segment_distance_threshold (float, optional): the threshold distance for noding issue detection. It is the distance between nodes and segments. Defaults to 0.1.
    """


    # list of issues
    issues = []

    print("load features")
    gdf = gpd.read_file(gpkg_path, bbox=bbox)

    # check OGC validity
    if check_ogc_validity:
        print("get feature geometries")
        mps = gdf["geometry"].geometry.tolist()
        print(len(mps), "feature geometries")

        print("check OGC validity")
        for g in mps:
            try:
                v = g.is_valid
                if not v:
                    issues.append(["Non valid geometry", "validity", g.centroid])
                # in addition, check effect of the buffer_0.
                # Buffer_0 operation cleans geometries. It removes duplicate vertices.
                g_ = g.buffer(0)
                if count_vertices(g) != count_vertices(g_):
                    issues.append(["Non valid geometry - buffer0", "validity_buffer0", g.centroid])
            except:
                continue
        del mps

    print("explode polygons")
    gdf = gdf.explode(index_parts=True)
    print(len(gdf), "polygons")


    if check_thin_parts:
        print("decompose multi polygons into simple polygons")
        polys = gdf.explode(index_parts=False)["geometry"]
        polys = polys.geometry.tolist()
        print(len(gdf), "polygons")

        print("check thin parts")
        for p in polys:
            try:
                # get eroded geometry
                p2 = p.buffer(-thin_part_threshold).buffer(thin_part_threshold)
                # compute hdistance to original geometry
                d = p.hausdorff_distance(p2)
                # if distance is small, continue
                if d < thin_part_threshold * 3: continue
                # compute difference
                diff = p.difference(p2)

                # convert into polygons
                if diff.geom_type == "Polygon": diff = [diff]
                else: diff = diff.geoms

                # check parts: raise issue for the large ones
                for part in diff:
                    a = part.area
                    if a < thin_part_threshold*thin_part_threshold * 7: continue
                    issues.append(["Thin polygon part. area="+str(a), "thin_polygon_part", part.centroid])
            except:
                continue


    if check_intersection:
        print("decompose multi polygons into simple polygons")
        polys = gdf.explode(index_parts=False)["geometry"]
        polys = polys.geometry.tolist()
        print(len(gdf), "polygons")

        print('make spatial index')
        items = []
        for i in range(len(polys)):
            g = polys[i]
            items.append((i, g.bounds, None))
        idx = index.Index(((i, box, obj) for i, box, obj in items))
        del items

        print("check intersection")
        for i in range(len(polys)):
            try:
                g = polys[i]
                intersl = list(idx.intersection(g.bounds))
                for j in intersl:
                    if i<=j: continue
                    gj = polys[j]
                    inte = g.intersects(gj)
                    if not inte: continue
                    inte = g.intersection(gj)
                    if inte.area == 0: continue
                    issues.append(["Polygon intersection - area="+str(inte.area), "intersection", inte.centroid])
            except:
                continue
        del polys

    print("get lines")
    gdf = gdf.geometry.boundary
    gdf = gdf.explode(index_parts=True)
    gdf = gdf.geometry.tolist()
    print(len(gdf), "lines")


    if check_polygonisation:
        # unionise lines, to remove duplicates
        # TODO: check without it ?
        print("unionise lines")
        lines = unary_union(gdf)
        lines = list(lines.geoms)
        print(len(lines), "lines")

        print("polygonise lines")
        polygons = list(polygonize(lines))
        print(len(polygons), "polygons after polygonisation")
        del lines

        print("check thin polygons")
        for poly in polygons:
            try:
                poly_ = poly.buffer(-polygonation_check_distance_threshold)
                if poly_.is_empty:
                    issues.append(["Thin polygon", "thin polygon", poly.centroid])
            except: continue
        del polygons


    if check_noding_issues or check_microscopic_segments:
        print("make list of segments and nodes")
        segments = []
        nodes = []
        for line in gdf:
            try:
                cs = list(line.coords)
                c0 = cs[0]
                nodes.append(Point(c0))
                for i in range(1, len(cs)):
                    c1 = cs[i]
                    nodes.append(Point(c1))
                    segments.append( LineString([c0, c1]) )
                    c0 = c1
            except: continue
        print(len(nodes), "nodes", len(segments), "segments")

        #TODO remove duplicate nodes and segments ?
        #gseries = gpd.GeoSeries(nodes)
        #nodes = gseries.drop_duplicates().tolist()
        #del gseries

    if check_microscopic_segments:
        print("check microscopic segments")
        for seg in segments:
            if seg.length < microscopic_segment_threshold:
                issues.append(["Microscopic segment. length =" + str(seg.length), "micro_segment", seg.centroid])

    if check_noding_issues:
        print("check noding issues")

        print('build index of nodes')
        items = []
        for i in range(len(nodes)):
            items.append((i, nodes[i].bounds, None))
        idx = index.Index(((i, box, obj) for i, box, obj in items))
        del items

        print("compute node to segment analysis")
        for seg in segments:
            try:
                candidate_nodes = idx.intersection(seg.bounds)
                #print(len(candidate_nodes))
                for cn in candidate_nodes:
                    cn = nodes[cn]
                    pos = nearest_points(cn, seg)[1]
                    dist = cn.distance(pos)
                    if dist == 0: continue
                    if dist > node_to_segment_distance_threshold: continue
                    #print(cn, dist)
                    issues.append(["Noding issue. dist =" + str(dist), "noding", cn])
            except: continue

    print("save issues as gpkg", len(issues))
    gdf = gpd.GeoDataFrame(issues, columns=["description", "type", "geometry"], crs="EPSG:3035" )
    gdf = gdf.drop_duplicates()
    print("    without duplicates:", len(gdf))
    if len(gdf) == 0: return
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

