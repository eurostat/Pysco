import numpy as np
#import rasterio
import shapely.geometry
import geopandas as gpd
from rtree import index


def make_land_1km_cells():
    'Make 1km grid cells that intersect land area of Iceland and save to geopackage.'

    # extent of iceland
    xmin, ymin, xmax, ymax = 2600000, 4700000, 3400000, 5300000

    # load iceland land area geometries from geopackage
    land_geometry = gpd.read_file(workspace + 'land_100k_decomposed.gpkg')
    land_geometry = land_geometry.geometry
    # build spatial index
    lg_index = index.Index()
    for i,g in enumerate(land_geometry): lg_index.insert(i, g.bounds)


    output_cells = []
    for x in range(xmin, xmax, 1000):
        print(x)
        for y in range(ymin, ymax, 1000):

            # get items using spatial index
            land_ = list(lg_index.intersection( (x, y, x + 1000, y + 1000) ))
            if len(land_) == 0: continue

            # make list of geometries from land_ids
            land = []
            for id in land_: land.append(land_geometry[id])
            # make union of land geometries
            land = shapely.ops.unary_union(land)

            # make cell geometry
            cell = shapely.geometry.box(x, y, x + 1000, y + 1000)

            cell = land.intersection(cell)
            if cell.area <= 0: continue

            inspire_id = f'CRS3035RES1000mN{int(y)}5{int(x)}'
            #print(f'Cell at ({x}, {y}) intersects land area with geometry: {intersection.area}')
            output_cells.append( { "geometry": cell, "GRD_ID": inspire_id, } )
    # save output cells to geopackage
    output_gdf = gpd.GeoDataFrame(output_cells, geometry='geometry', crs='EPSG:3035')
    output_gdf.to_file(workspace + 'out/land_1km_cells.gpkg', driver='GPKG')



# from a shapely geometry, make n random point geometries within the area
def random_points_within(geometry, n):
    'Generate n random points within a given shapely geometry area.'
    minx, miny, maxx, maxy = geometry.bounds
    points = []
    randuni = np.random.uniform
    pt = shapely.geometry.Point
    while len(points) < n:
        random_point = pt(randuni(minx, maxx), randuni(miny, maxy))
        if geometry.contains(random_point): points.append(random_point)
    return points


def dasymetric_disaggregation_step_1(input_pop_gpkg, input_dasymetric_gpkg, pop_att, output_gpkg, output_points_gpkg=None):
    'Disaggregate population units to dasymetric areas and optionally generate random points.'

    # load dasymetric geometries
    gdf_dasymetric = gpd.read_file(input_dasymetric_gpkg).geometry
    # build spatial index
    das_index = index.Index()
    for i,g in enumerate(gdf_dasymetric): das_index.insert(i, g.bounds)

    # load population units
    gdf = gpd.read_file(input_pop_gpkg)

    # outputs
    output_areas = []; output_points = []

    # process each population unit
    for _, row in gdf.iterrows():

        # get population and geometry
        pop = int(row[pop_att])
        if pop is None or pop <= 0: continue
        g = row.geometry

        # get dasymetric indexes using spatial index
        das = list(das_index.intersection(g.bounds))

        if len(das) == 0:
            print('No dasymetric area found for unit with population:', pop, "around point", g.representative_point())
            continue

        # make list of dasymetric geometries
        das_g = []
        for id in das: das_g.append(gdf_dasymetric[id])
        # make union
        das_g = shapely.ops.unary_union(das_g)
        das = None

        # compute intersection
        inter = g.intersection(das_g)
        if inter.area <= 0:
            print('No dasymetric area found for unit with population:', pop, "around point", g.representative_point())
            continue
        g = inter

        # output areas
        output_areas.append( { "geometry": g, pop_att:pop } )

        # generate random points within geometry
        if output_points_gpkg is not None:
            points = random_points_within(g, pop)
            for point in points:
                output_points.append( { "geometry": point } )

    # save output areas
    gpd.GeoDataFrame(output_areas, geometry='geometry', crs=gdf.crs).to_file(output_gpkg, driver='GPKG')

    if output_points_gpkg is not None:
        # save output points
        gpd.GeoDataFrame(output_points, geometry='geometry', crs=gdf.crs).to_file(output_points_gpkg, driver='GPKG')




def dasymetric_aggregation_step_2(input_das_gpkg, pop_att, output_gpkg):
    'Aggregate population from dasymetric areas to grid cells.'

    # load dasymetric areas
    gdf_das = gpd.read_file(input_das_gpkg)
    # build spatial index
    das_index = index.Index()
    for i,f in enumerate(gdf_das): das_index.insert(i, f.geometry.bounds)

    # get bounds of all geometries
    (minx, miny, maxx, maxy) = gdf_das.total_bounds
    minx = int(minx // 1000 * 1000)
    miny = int(miny // 1000 * 1000)

    output_cells = []
    for x in range(minx, maxx+1000, 1000):
        print(x)
        for y in range(miny, maxy+1000, 1000):

            # get dasymetric indexes using spatial index
            das = list(das_index.intersection(g.bounds))

            if len(das) == 0: continue

            # make cell geometry
            cell = shapely.geometry.box(x, y, x + 1000, y + 1000)

            cell_pop = 0
            for id in das:
                # get dasymetric feature
                das_f = gdf_das[id]

                # get population
                das_pop = 1 if pop_att==None else das_f[pop_att]
                if das_pop is None or das_pop <= 0: continue

                # check if geometry type of das_f.geometry is a point
                if das_f.geometry.geom_type == 'Point':
                    if cell.contains(das_f.geometry): cell_pop += das_pop
                    continue

                area = das_f.geometry.area
                if area <= 0: continue
                inter = cell.intersection(das_f.geometry)
                if inter.area <= 0: continue
                cell_pop += das_pop * (inter.area / area)

            # output areas
            output_cells.append( { "geometry": cell, pop_att:cell_pop } )

    # save output cells
    gpd.GeoDataFrame(output_cells, geometry='geometry', crs=gdf_das.crs).to_file(output_gpkg, driver='GPKG')




w = '/home/juju/gisco/census_2021_iceland/'

dasymetric_disaggregation_step_1(
    w+"pop_test.gpkg",
    w+"clc_urban.gpkg", # land_100k_decomposed clc_urban
    "popul",
    w+"out/disac_area.gpkg",
    w+"out/disac_point.gpkg",
)

dasymetric_aggregation_step_2()


#dasymetric_disaggregation_step_1()





'''
# nearest neighbor resampling
def nn_resample(src, dst, scale):
    'Nearest neighbor resampling from src to dst with given scale factor.'

    src_h, src_w = src.shape
    dst_h, dst_w = dst.shape

    for i in range(dst_h):
        for j in range(dst_w):
            src_i = min(int(i * scale), src_h - 1)
            src_j = min(int(j * scale), src_w - 1)
            dst[i, j] = src[src_i, src_j]

    return dst


# load grid data from tiff file
def load_grid_data(tiff_path):  
    'Load grid data from a tiff file and return as a numpy array.'

    with rasterio.open(tiff_path) as src:
        data = src.read(1)  # Read the first band

        # convert pixels to shapely geometries
        array = np.array(data)
'''

