import geopandas as gpd
from rtree import index
from shapely.ops import polygonize, unary_union


def check_validity(gpkg_path):
    print("load")
    gdf = gpd.read_file(gpkg_path)["geometry"]
    gdf = gdf.geometry.tolist()

    for g in gdf:
        v = g.is_valid
        if v: continue
        print("Non valide geometry around: ", g.centroid)



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




gf = "/home/juju/Bureau/jorge_stuff/AU_NO_SE_FI_V.gpkg"
check_validity(gf)
#check_intersections(gf)
#check_polygonise(gf)

