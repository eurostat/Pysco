import geopandas as gpd
from rtree import index
from shapely.ops import polygonize, unary_union


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


def polyg(gpkg_path):

    # get polygon contours
    gdf = gpd.read_file(gpkg_path)
    gdf = gdf.explode(index_parts=True)
    gdf = gdf.geometry.boundary
    gdf = gdf.geometry.tolist()
    print(len(gdf), "lines")

    gdf = unary_union(gdf)
    print(len(gdf), "lines")

    polygons = list(polygonize(gdf))

    print(len(polygons), "polygons")

    for poly in polygons:
        poly = poly.buffer(-0.001)
        if poly.is_empty:
            print("found")
            print(poly.centroid)




gf = "/home/juju/Bureau/jorge_stuff/AU_NO_SE_FI_V.gpkg"
#check_intersections(gf)
polyg(gf)
