import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import box
import numpy as np
from math import floor



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



def intersect_with_grid(input_gpkg, grid_resolution, output_gpkg):
    # load input file
    gdf = gpd.read_file(input_gpkg)

    # bounds
    minx, miny, maxx, maxy = gdf.total_bounds
    minx = floor(minx/grid_resolution)*grid_resolution
    miny = floor(miny/grid_resolution)*grid_resolution

    # make grid
    x_coords = np.arange(minx, maxx, grid_resolution)
    y_coords = np.arange(miny, maxy, grid_resolution)

    # make grid cells
    grid_cells = []
    for x in x_coords:
        for y in y_coords:
            cell = box(x, y, x + grid_resolution, y + grid_resolution)
            grid_cells.append(cell)
    del x_coords
    del y_coords

    # make grid
    grid_gdf = gpd.GeoDataFrame(geometry=grid_cells, crs=gdf.crs)

    # compute intersection
    intersected_gdf = gpd.overlay(gdf, grid_gdf, how='intersection')

    # save output
    intersected_gdf.to_file(output_gpkg, driver='GPKG')


#ccs = [ "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "EL", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE", "AD", "SM", "MC", "VA", "NO", "CH" ]
#make_landmass_polygons("/home/juju/geodata/gisco/CNTR_RG_100K_2024_3035.gpkg", "/home/juju/gisco/road_transport_performance/land_mass.gpkg", "CNTR_ID", ccs)

intersect_with_grid("/home/juju/gisco/road_transport_performance/land_mass.gpkg", 100000, "/home/juju/gisco/road_transport_performance/land_mass_grid.gpkg")
