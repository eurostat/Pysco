import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import box,Point, Polygon
import numpy as np
from math import floor

# make union of polygon, and decompose the union into simple polygon features tagged with a unique code
def make_landmass_polygons(input_file, output_file, id_att, id_values):

    # load gpkg
    gdf = gpd.read_file(input_file)
    crs = gdf.crs
    print(gdf.size, "loaded")

    # filter
    gdf = gdf[gdf[id_att].isin(id_values)]
    print(gdf.size, "filtered")

    # keep geometries
    gdf = gdf.geometry

    print("compute union")
    u = unary_union(gdf)
    del gdf

    print("decompose")
    simple_polygons = []
    if u.geom_type == 'Polygon':
        simple_polygons.append(u)
    elif u.geom_type == 'MultiPolygon':
        simple_polygons.extend(list(u.geoms))
    del u

    # make geodataframe
    result_gdf = gpd.GeoDataFrame(geometry=simple_polygons, crs=crs)

    # add code
    result_gdf['code'] = range(1, len(result_gdf) + 1)

    print("save")
    result_gdf.to_file(output_file, driver='GPKG')


# intersect a dataset with a grid
def intersect_with_grid(input_gpkg, grid_resolution, output_gpkg):

    # load input file
    gdf = gpd.read_file(input_gpkg)
    print(gdf.size, "loaded")

    # bounds
    minx, miny, maxx, maxy = gdf.total_bounds
    minx = floor(minx/grid_resolution)*grid_resolution
    miny = floor(miny/grid_resolution)*grid_resolution

    # make grid
    x_coords = np.arange(minx, maxx, grid_resolution)
    y_coords = np.arange(miny, maxy, grid_resolution)

    print("make grid")
    grid_cells = []
    for x in x_coords:
        for y in y_coords:
            cell = box(x, y, x + grid_resolution, y + grid_resolution)
            grid_cells.append(cell)
    del x_coords
    del y_coords

    grid_gdf = gpd.GeoDataFrame(geometry=grid_cells, crs=gdf.crs)
    del grid_cells

    print("compute grid intersection")
    gdf = gpd.overlay(gdf, grid_gdf, how='intersection')
    print(gdf.size)
    del grid_gdf

    print("decompose multipolygons")
    gdf = gdf.explode(index_parts=True)
    gdf = gdf.reset_index(drop=True)

    print("save", gdf.size)
    gdf.to_file(output_gpkg, driver='GPKG')


def tag_grid_cells(id_att, id_values):

    # load cells
    points = gpd.read_file("/home/juju/geodata/gisco/grids/grid_1km_point.gpkg")
    print(points.size, "cells loaded")

    # filter
    gdf = gdf[gdf[id_att].isin(id_values)]
    print(gdf.size, "filtered")

    # load land mass polygons
    lm_polygons = gpd.read_file("/home/juju/gisco/road_transport_performance/land_mass_gridded.gpkg")
    print(lm_polygons.size, "loaded")

    # spatial join
    result = gpd.sjoin(points, lm_polygons, how="inner", predicate="within")

    # save result
    print("save", result.size)
    result.to_file("/home/juju/gisco/road_transport_performance/pop_land_mass_"+str(year)+".gpkg", driver='GPKG')



ccs = [ "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "EL", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE", "AD", "SM", "MC", "VA", "NO", "CH" ]
#make_landmass_polygons("/home/juju/geodata/gisco/CNTR_RG_100K_2024_3035.gpkg", "/home/juju/gisco/road_transport_performance/land_mass.gpkg", "CNTR_ID", ccs)

#intersect_with_grid("/home/juju/gisco/road_transport_performance/land_mass.gpkg", 10000, "/home/juju/gisco/road_transport_performance/land_mass_gridded.gpkg")

tag_grid_cells("CNTR_ID", css)

