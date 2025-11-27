import numpy as np
import shapely.geometry
import geopandas as gpd
from rtree import index
import random
from collections import Counter, defaultdict


#TODO handle categories
#TODO handle categories - generic
#TODO cas_l_1_1
#TODO validate
#TODO test with 100m

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


def count_categories(population, categories=[], tot="count", sort=True):
    """
    population : list of dicts produced by your synthetic generator
    categories     : list of category names to count

    Returns a dictionary: { field_name: count }
    """

    #stats = { cat: {} for cat in categories }
    stats = {}
    for person in population:
        for cat in categories:
            mode = person.get(cat)
            if mode is None: continue
            #if mode in stats[cat]: stats[cat][mode] = stats[cat][mode] + 1
            #else: stats[cat][mode] = 1
            if mode in stats: stats[mode] = stats[mode] + 1
            else: stats[mode] = 1
    # sort
    if sort: stats = { k: stats[k] for k in sorted(stats) }
    stats[tot] = len(population)
    return stats




def dasymetric_disaggregation_step_1(input_pop_gpkg, input_dasymetric_gpkg, pop_att, output_gpkg, output_synthetic_population_gpkg=None, pop_atts=[]):
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
        f = { "geometry": g, pop_att: pop }
        for att in pop_atts: f[att] = row.get(att)
        output_areas.append(f)

        # generate random points within geometry
        if output_synthetic_population_gpkg is not None:
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



def dasymetric_aggregation_step_2(input_das_gpkg, pop_att, output_gpkg, categories=[], pop_atts=[], geom_type='Polygon', resolution=1000):
    'Aggregate population from dasymetric areas or points to grid cells.'

    # load dasymetric areas
    gdf_das = gpd.read_file(input_das_gpkg)
    # build spatial index
    das_index = index.Index()
    for i, f in gdf_das.iterrows(): das_index.insert(i, f['geometry'].bounds)

    # get bounds of all geometries
    (minx, miny, maxx, maxy) = gdf_das.total_bounds
    minx = int(minx // resolution * resolution)
    miny = int(miny // resolution * resolution)
    maxx = int(maxx // resolution * resolution) + resolution
    maxy = int(maxy // resolution * resolution) + resolution

    output_cells = []
    #out_pop_att = "sex_0" if pop_att==None else pop_att
    for x in range(minx, maxx, resolution):
        for y in range(miny, maxy, resolution):

            # get dasymetric indexes using spatial index
            das = list(das_index.intersection((x, y, x + resolution, y + resolution)))

            if len(das) == 0: continue

            # make cell
            cell_g = shapely.geometry.box(x, y, x + resolution, y + resolution)
            cell = { "geometry": cell_g, pop_att: 0 }
            for att in pop_atts: cell[att] = 0

            if geom_type == 'Point':
                # get population
                population = []
                for id in das:
                    person = gdf_das.iloc[id]
                    if cell_g.contains(person["geometry"]): population.append(person)

                # get population counts
                stats = count_categories(population, categories=categories, tot=pop_att, sort=True)

                # do not store empty cells
                if stats[pop_att] <= 0: continue

                # set cell statistics
                cell[pop_att] = stats[pop_att]
                for att in pop_atts:
                    if att in stats: cell[att] = cell[att]

            else:

                for id in das:
                    # get dasymetric feature
                    das_f = gdf_das.iloc[id]

                    # get population
                    das_pop = 1 if pop_att==None else das_f[pop_att]
                    if das_pop is None or das_pop <= 0: continue

                    # check if geometry type of das_f.geometry is a point
                    g = das_f.geometry
                    if g.geom_type == 'Point':
                        if cell_g.contains(g): cell_pop += das_pop
                        continue

                    area = g.area
                    if area <= 0: continue
                    inter = cell_g.intersection(g)
                    if inter.area <= 0: continue
                    cell_pop += das_pop * (inter.area / area)

                    # do not store empty cells
                    if cell[pop_att] <= 0: continue

            # output cells
            output_cells.append(cell)

    # save output cells
    gpd.GeoDataFrame(output_cells, geometry='geometry', crs=gdf_das.crs).to_file(output_gpkg, driver='GPKG')





w = '/home/juju/gisco/census_2021_iceland/'
categories = ["sex", "age_g", "pob_l", "roy"]
pop_atts = ["sex_1", "sex_2", "age_g_1", "age_g_2", "age_g_3", "cas_l_1_1", "pob_l_1", "pob_l_2_1", "pob_l_2_2", "roy_1", "roy_2_1", "roy_2_2"]

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
dasymetric_disaggregation_step_1(
    w+"IS_pop_grid_surf_3035_land.gpkg",
    w+"ghsl_land_3035.gpkg", # strandlina_flakar_3035_decomposed clc_urban
    "sex_0",
    w+"out/disag_area_ghsl_land.gpkg",
    w+"out/disag_point_ghsl_land.gpkg",
    pop_atts=pop_atts,
)
'''



'''
print("Dasymetric aggregation step 2")
dasymetric_aggregation_step_2(w+"out/disag_area.gpkg", "sex_0", w+"out/area_weighted.gpkg", pop_atts=pop_atts)
dasymetric_aggregation_step_2(w+"out/disag_area_land.gpkg", "sex_0", w+"out/dasymetric_land.gpkg", pop_atts=pop_atts)
dasymetric_aggregation_step_2(w+"out/disag_area_ghsl_land.gpkg", "sex_0", w+"out/dasymetric_GHSL_land.gpkg", pop_atts=pop_atts)
'''
print("Dasymetric aggregation step 2 from points")
#dasymetric_aggregation_step_2(w+"out/disag_point.gpkg", "sex_0", w+"out/area_weighted_rounded.gpkg", geom_type='Point', pop_atts=pop_atts)
#dasymetric_aggregation_step_2(w+"out/disag_point_land.gpkg", "sex_0", w+"out/dasymetric_land_rounded.gpkg", geom_type='Point', pop_atts=pop_atts)
dasymetric_aggregation_step_2(w+"out/disag_point_ghsl_land.gpkg", "sex_0", w+"out/dasymetric_GHSL_land_rounded.gpkg", geom_type='Point', pop_atts=pop_atts, categories=categories)

#print("Nearest neighbour")
#dasymetric_aggregation_step_2(w+"IS_pop_grid_point_3035.gpkg", "sex_0", w+"out/nearest_neighbour.gpkg")

