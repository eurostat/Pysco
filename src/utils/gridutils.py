import csv
from shapely.geometry import Polygon, box
import geopandas as gpd
import numpy as np
from math import floor, ceil

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





def gridify_gpkg(input_gpkg_path, grid_spacing, output_gpkg_path):
    # Load the input GeoPackage file
    gdf = gpd.read_file(input_gpkg_path)

    # Determine the bounds of the input features
    minx, miny, maxx, maxy = gdf.total_bounds

    # Clamp
    minx = floor(minx/grid_spacing) * grid_spacing
    miny = floor(miny/grid_spacing) * grid_spacing
    maxx = ceil(maxx/grid_spacing) * grid_spacing
    maxy = ceil(maxy/grid_spacing) * grid_spacing

    # Create a grid
    grid_cells = []
    x_coords = np.arange(minx, maxx, grid_spacing)
    y_coords = np.arange(miny, maxy, grid_spacing)

    for x in x_coords:
        for y in y_coords:
            # Create a grid cell polygon
            cell = box(x, y, x + grid_spacing, y + grid_spacing)
            grid_cells.append(cell)

    # Create a GeoDataFrame for the grid
    grid_gdf = gpd.GeoDataFrame(geometry=grid_cells, crs=gdf.crs)

    # Perform spatial intersection
    out = gpd.overlay(gdf, grid_gdf, how='intersection')
    del grid_gdf

    # Explode MultiPolygons into Polygons
    out = out.explode(index_parts=False)

    # Reset index to avoid index duplication after explode
    out = out.reset_index(drop=True)

    # Save the result to the output GeoPackage file
    out.to_file(output_gpkg_path, driver='GPKG')

