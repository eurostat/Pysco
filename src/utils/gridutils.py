import csv
from shapely.geometry import Polygon

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import save_features_to_gpkg, get_schema_from_feature


def csv_grid_to_geopackage(csv_grid_path, gpkg_grid_path, geom="surf"):

    #load csv
    data = None
    with open(csv_grid_path, mode="r", newline="") as file:
        reader = csv.DictReader(file)
        data = list(reader)

    for c in data:

        #grid_id to x,y
        a = c['GRD_ID'].split("N")[1].split("E")
        x = int(a[1])
        y = int(a[0])

        #make grid cell geometry
        grid_resolution = 1000
        c["geometry"] = Polygon([(x, y), (x+grid_resolution, y), (x+grid_resolution, y+grid_resolution), (x, y+grid_resolution)])

        save_features_to_gpkg(data, gpkg_grid_path)

