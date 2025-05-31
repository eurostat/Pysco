import csv
from shapely.geometry import Polygon

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import save_features_to_gpkg, get_schema_from_feature


def get_cell_xy_from_id(id):
    a = id.split("N")[1].split("E")
    return [int(a[1]), int(a[0])]


#CRS3035RES100mN2951100E4039900

def get_cell_id(res_m, crs, x, y):
    return 'CRS' + str(crs) + 'RES' + str(res_m) + 'mN' + str(int(y)) + 'E' + str(int(x))



def csv_grid_to_geopackage(csv_grid_path, gpkg_grid_path, geom="surf"):

    #load csv
    data = None
    with open(csv_grid_path, mode="r", newline="") as file:
        reader = csv.DictReader(file)
        data = list(reader)

    #save as gpkg
    grid_to_geopackage(data, gpkg_grid_path, geom)



def grid_to_geopackage(cells, gpkg_grid_path, geom="surf"):

    #make grid cell geometry
    for c in cells:
        [x, y] = get_cell_xy_from_id(c['GRD_ID'])
        grid_resolution = 1000
        c['geometry'] = Polygon([(x, y), (x+grid_resolution, y), (x+grid_resolution, y+grid_resolution), (x, y+grid_resolution)])

    #save as gpkg
    save_features_to_gpkg(cells, gpkg_grid_path)

