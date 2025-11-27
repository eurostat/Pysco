import numpy as np
import shapely.geometry
import geopandas as gpd
from rtree import index
import random
from collections import Counter, defaultdict


#TODO handle categories
#TODO handle categories - generic
#TODO cas_l_1_1
#TODO GHSL: improve, with probability?
#TODO OSM buildings ?


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

# make a synthetic population of n persons
def make_synthetic_population(n, data, check_counts=True):

    # build lists
    lists = {}
    lists['sex'] = (
        ["sex_1"] * data.get("sex_1", 0) +
        ["sex_2"] * data.get("sex_2", 0)
    )
    lists['age_g'] = (
        ["age_g_1"] * data.get("age_g_1", 0) +
        ["age_g_2"] * data.get("age_g_2", 0) +
        ["age_g_3"] * data.get("age_g_3", 0)
    )
    lists['pob_l'] = (
        ["pob_l_1"] * data.get("pob_l_1", 0) +
        ["pob_l_2_1"] * data.get("pob_l_2_1", 0) +
        ["pob_l_2_2"] * data.get("pob_l_2_2", 0)
    )
    lists['roy'] = (
        ["roy_1"] * data.get("roy_1", 0) +
        ["roy_2_1"] * data.get("roy_2_1", 0) +
        ["roy_2_2"] * data.get("roy_2_2", 0)
    )

    # check totals
    if check_counts:
        for cat in ["sex", "age_g", "pob_l", "roy"]:
            if len(lists[cat]) != n:
                #print(data)
                print("Counts in data do not sum to n", cat, len(lists[cat]), n)

    # shuffle
    for cat in ["sex", "age_g", "pob_l", "roy"]:
        random.shuffle(lists[cat])

    # make population
    population = []
    for i in range(n):
        # make person
        person = {}
        # fill categories
        for cat in ["sex", "age_g", "pob_l", "roy"]:
            if i>=len(lists[cat]): person[cat] = None
            else: person[cat] = lists[cat][i]
        # add to population
        population.append(person)

    return population


def count_categories(population, categories):
    """
    population : list of dicts produced by your synthetic generator
    categories     : list of category names to count

    Returns a dictionary: { field_name: count }
    """

    stats = { cat: {} for cat in categories }
    for person in population:
        for cat in categories:
            mode = person.get(cat)
            if mode is None: continue
            if mode in stats[cat]: stats[cat][mode] = stats[cat][mode] + 1
            else: stats[cat][mode] = 1
    return stats




def dasymetric_disaggregation_step_1(input_pop_gpkg, input_dasymetric_gpkg, pop_att, output_gpkg, output_synthetic_population_gpkg=None):
    'Disaggregate population units to dasymetric areas and optionally generate random points.'

    # load dasymetric geometries
    gdf_dasymetric = gpd.read_file(input_dasymetric_gpkg).geometry
    # build spatial index
    das_index = index.Index()
    for i,g in enumerate(gdf_dasymetric): das_index.insert(i, g.bounds)

    # load population units
    gdf = gpd.read_file(input_pop_gpkg)

    # outputs
    output_areas = []; output_synthetic_population = []

    # process each population unit
    for _, row in gdf.iterrows():

        # get population and geometry
        pop = int(row[pop_att])
        if pop is None or pop <= 0: continue
        g = row.geometry

        # get dasymetric indexes using spatial index
        das = list(das_index.intersection(g.bounds))

        #if len(das) == 0:
        #    print('No dasymetric area found for unit with population:', pop, "around point", g.representative_point())
        #    continue

        # make list of dasymetric geometries
        das_g = []
        for id in das: das_g.append(gdf_dasymetric[id])
        # make union
        das_g = shapely.ops.unary_union(das_g)
        das = None

        # compute intersection
        inter = g.intersection(das_g)
        if inter.area <= 0:
            #print('No dasymetric area found for unit with population:', pop, "around point", g.representative_point())
            # use entire origin geometry
            inter = g
        g = inter

        # output areas
        output_areas.append( { "geometry": g, pop_att:pop } )

        # generate random points within geometry
        if output_synthetic_population_gpkg is not None:
            output_synthetic_population = []
            # make synthetic population
            sp = make_synthetic_population(pop, row, check_counts=False)
            # make random locations within geometry
            points = random_points_within(g, pop)
            # put localisation to each person
            for i in range(pop): sp[i]['geometry'] = points[i]
            #
            output_synthetic_population.extend(sp)

    # save output areas
    gpd.GeoDataFrame(output_areas, geometry='geometry', crs=gdf.crs).to_file(output_gpkg, driver='GPKG')

    if output_synthetic_population_gpkg is not None:
        # save output points
        gpd.GeoDataFrame(output_synthetic_population, geometry='geometry', crs=gdf.crs).to_file(output_synthetic_population_gpkg, driver='GPKG')




def dasymetric_aggregation_step_2(input_das_gpkg, pop_att, output_gpkg):
    'Aggregate population from dasymetric areas or points to grid cells.'

    # load dasymetric areas
    gdf_das = gpd.read_file(input_das_gpkg)
    # build spatial index
    das_index = index.Index()
    for i, f in gdf_das.iterrows(): das_index.insert(i, f['geometry'].bounds)

    # get bounds of all geometries
    (minx, miny, maxx, maxy) = gdf_das.total_bounds
    minx = int(minx // 1000 * 1000)
    miny = int(miny // 1000 * 1000)
    maxx = int(maxx // 1000 * 1000) + 1000
    maxy = int(maxy // 1000 * 1000) + 1000

    output_cells = []
    out_pop_att = "sex_0" if pop_att==None else pop_att
    for x in range(minx, maxx, 1000):
        for y in range(miny, maxy, 1000):

            # get dasymetric indexes using spatial index
            das = list(das_index.intersection((x, y, x + 1000, y + 1000)))

            if len(das) == 0: continue

            # make cell geometry
            cell = shapely.geometry.box(x, y, x + 1000, y + 1000)

            cell_pop = 0
            for id in das:
                # get dasymetric feature
                das_f = gdf_das.iloc[id]

                # get population
                das_pop = 1 if pop_att==None else das_f[pop_att]
                if das_pop is None or das_pop <= 0: continue

                # check if geometry type of das_f.geometry is a point
                g = das_f.geometry
                if g.geom_type == 'Point':
                    if cell.contains(g): cell_pop += das_pop
                    continue

                area = g.area
                if area <= 0: continue
                inter = cell.intersection(g)
                if inter.area <= 0: continue
                cell_pop += das_pop * (inter.area / area)

            if cell_pop <= 0: continue

            # output areas
            output_cells.append( { "geometry": cell, out_pop_att: cell_pop } )

    # save output cells
    gpd.GeoDataFrame(output_cells, geometry='geometry', crs=gdf_das.crs).to_file(output_gpkg, driver='GPKG')





w = '/home/juju/gisco/census_2021_iceland/'

'''
# GHSL to vector
raster_pixels_above_threshold_to_gpkg(
    ['/home/juju/geodata/IS/GHS_BUILT_S_E2020_GLOBE_R2023A_54009_100_V1_0_R2_C17.tif', '/home/juju/geodata/IS/GHS_BUILT_S_E2020_GLOBE_R2023A_54009_100_V1_0_R2_C18.tif'],
    1, w+'out/ghsl.gpkg')
'''

print("Dasymetric disaggregation step 1")
'''
dasymetric_disaggregation_step_1(
    w+"IS_pop_grid_surf_3035.gpkg",
    w+"IS_pop_grid_surf_3035.gpkg", # strandlina_flakar_3035_decomposed clc_urban
    "sex_0",
    w+"out/disag_area.gpkg",
    w+"out/disag_point.gpkg",
)
dasymetric_disaggregation_step_1(
    w+"IS_pop_grid_surf_3035_land.gpkg",
    w+"strandlina_flakar_3035_decomposed.gpkg", # strandlina_flakar_3035_decomposed clc_urban
    "sex_0",
    w+"out/disag_area_land.gpkg",
    w+"out/disag_point_land.gpkg",
)
'''
dasymetric_disaggregation_step_1(
    w+"IS_pop_grid_surf_3035_land.gpkg",
    w+"ghsl_land_3035.gpkg", # strandlina_flakar_3035_decomposed clc_urban
    "sex_0",
    w+"out/disag_area_ghsl_land.gpkg",
    w+"out/disag_point_ghsl_land.gpkg",
)

'''
print("Dasymetric aggregation step 2")
dasymetric_aggregation_step_2(w+"out/disag_area.gpkg", "sex_0", w+"out/area_weighted.gpkg")
dasymetric_aggregation_step_2(w+"out/disag_area_land.gpkg", "sex_0", w+"out/dasymetric_land.gpkg")
dasymetric_aggregation_step_2(w+"out/disag_area_ghsl_land.gpkg", "sex_0", w+"out/dasymetric_GHSL_land.gpkg")
'''
print("Dasymetric aggregation step 2 from points")
#dasymetric_aggregation_step_2(w+"out/disag_point.gpkg", None, w+"out/area_weighted_rounded.gpkg")
#dasymetric_aggregation_step_2(w+"out/disag_point_land.gpkg", None, w+"out/dasymetric_land_rounded.gpkg")
#dasymetric_aggregation_step_2(w+"out/disag_point_ghsl_land.gpkg", None, w+"out/dasymetric_GHSL_land_rounded.gpkg")

#print("Nearest neighbour")
#dasymetric_aggregation_step_2(w+"IS_pop_grid_point_3035.gpkg", "sex_0", w+"out/nearest_neighbour.gpkg")







'''
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
'''



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

