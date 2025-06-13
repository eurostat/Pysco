import geopandas as gpd
from rtree import index

import geopandas as gpd
from rtree import index

def check_overlaps(gpkg_path):
    print("load")
    gdf = gpd.read_file(gpkg_path)

    print("decompose to polygons")
    gdf = gdf.explode(index_parts=False)["geometry"]

    print('build index')
    idx = index.Index()
    for idx_val, geometry in enumerate(gdf.geometry):
        idx.insert(idx_val, geometry.bounds)

    print("check overlaps")
    overlaps = set()
    for geom_id in range(len(gdf)):
        print(geom_id)
        for other_geom_id in list(idx.intersection(gdf.geometry[geom_id].bounds)):
            if geom_id != other_geom_id and gdf.geometry[geom_id].overlaps(gdf.geometry[other_geom_id]):
                overlaps.add((geom_id, other_geom_id))

    if overlaps:
        print("Overlaps detected.")
        return True
    else:
        print("No overlaps detected.")
        return False



gf = "/home/juju/Bureau/jorge_stuff/AU_NO_SE_FI_V.gpkg"
check_overlaps(gf)

