import numpy as np
import shapely.geometry
import geopandas as gpd
from rtree import index
import random
from shapely.geometry import Polygon


# from a shapely geometry, make n random point geometries within the area
def random_points_within(geometry, nb):
    """
    Generate nb random points within a shapely geometry area.
    """
    minx, miny, maxx, maxy = geometry.bounds
    points = []
    randuni = np.random.uniform
    pt = shapely.geometry.Point
    while len(points) < nb:
        random_point = pt(randuni(minx, maxx), randuni(miny, maxy))
        if geometry.contains(random_point): points.append(random_point)
    return points


def centroid_of_largest_hull(geometry):
    """
    Return the centroid of the convex hull of the largest polygon contained in a Polygon or MultiPolygon geometry.
    """
    if geometry.is_empty: return None
    if isinstance(geometry, Polygon): return geometry.convex_hull.centroid
    poly = max(list(geometry.geoms), key=lambda p: p.area)
    return poly.convex_hull.centroid


# make a synthetic population of n persons
#structure = { "sex" : ["sex_1", "sex_2"], "age_g" : ["age_g_1","age_g_2","age_g_3"], "pob_l" : ["pob_l_1","pob_l_2_1","pob_l_2_2"], "roy" : ["roy_1","roy_2_1","roy_2_2"] }
def make_synthetic_population(n, data, pop_structure, check_counts=True):

    # build list of values
    lists = {}
    for key, labels in pop_structure.items():
        result = []
        for label in labels: result.extend([label] * data.get(label, 0))
        lists[key] = result

    #
    categories = pop_structure.keys()

    # check totals
    if check_counts:
        for cat in categories:
            if len(lists[cat]) != n:
                #print(data)
                print("Counts in data do not sum to n", cat, len(lists[cat]), n)

    # shuffle
    for cat in categories:
        random.shuffle(lists[cat])

    # make population
    population = []
    for i in range(n):
        # make person
        person = {}
        # fill categories
        for cat in categories:
            if i>=len(lists[cat]): person[cat] = None
            else: person[cat] = lists[cat][i]
        # add to population
        population.append(person)

    return population


def count_categories(population, categories=[], tot_pop_att="TOT_POP", sort=True):
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
    stats[tot_pop_att] = len(population)
    return stats




def dasymetric_disaggregation_step_1(input_pop_gpkg, input_dasymetric_gpkg, output_gpkg, output_synthetic_population_gpkg=None, tot_pop_att = "TOT_POP", pop_structure = {}, pop_grouping_threshold=6):
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
        pop = int(row[tot_pop_att])
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
        f = { "geometry": g, tot_pop_att: pop }

        for atts in pop_structure.values():
            for att in atts: f[att] = row.get(att)
        output_areas.append(f)

        # generate random points within geometry
        if output_synthetic_population_gpkg is not None:

            # make synthetic population
            sp = make_synthetic_population(pop, row, pop_structure, check_counts=False)

            # move persons to random locations
            if pop <= pop_grouping_threshold:
                # small population, put all at the centroid
                # pt = g.representative_point()
                pt = centroid_of_largest_hull(g)
                for i in range(pop): sp[i]['geometry'] = pt
            else:
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



def dasymetric_aggregation_step_2(input_das_gpkg, output_gpkg, tot_pop_att = "TOT_POP", pop_structure = {}, type='area', resolution=1000):
    'Aggregate population from dasymetric areas or points to grid cells.'
    'type: "area" or "point" or "population"'

    # load dasymetric features
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

    # list of population attribute
    pop_atts = []
    for atts in pop_structure.values(): pop_atts.extend(atts)

    output_cells = []
    for x in range(minx, maxx, resolution):
        for y in range(miny, maxy, resolution):

            # get dasymetric indexes using spatial index
            das = list(das_index.intersection((x, y, x + resolution, y + resolution)))

            if len(das) == 0: continue

            # make cell
            cell_g = shapely.geometry.box(x, y, x + resolution, y + resolution)
            cell = { "geometry": cell_g, tot_pop_att: 0 }
            for att in pop_atts: cell[att] = 0

            if type == 'population':

                # get population
                population = []
                for id in das:
                    person = gdf_das.iloc[id]
                    if cell_g.contains(person["geometry"]): population.append(person)

                # get population counts
                stats = count_categories(population, categories=pop_structure.keys(), tot_pop_att=tot_pop_att, sort=True)

                # do not store empty cells
                if stats[tot_pop_att] <= 0: continue

                # set cell statistics
                cell[tot_pop_att] = stats[tot_pop_att]
                for att in pop_atts:
                    if att in stats: cell[att] = stats[att]

            else:
                # area or point case

                for id in das:
                    # get dasymetric feature
                    das_f = gdf_das.iloc[id]

                    # get its population
                    das_pop = das_f[tot_pop_att]
                    if das_pop is None or das_pop <= 0: continue

                    # get geometry
                    g = das_f.geometry

                    # compute share
                    if type == 'area':
                        area = g.area
                        if area <= 0: continue
                        share = cell_g.intersection(g).area / area
                    elif type == 'point':
                        share = 1 if cell_g.contains(g) else 0
                    else: raise Exception("Unknown type: "+str(type))

                    if share <= 0: continue

                    # compute population to assign
                    cell[tot_pop_att] += das_pop * share
                    for att in pop_atts:
                        das_att = das_f.get(att)
                        if das_att is None or das_att <= 0: continue
                        cell[att] += das_att * share

            if cell[tot_pop_att]<=0: continue

            # output cells
            output_cells.append(cell)

    # save output cells
    gpd.GeoDataFrame(output_cells, geometry='geometry', crs=gdf_das.crs).to_file(output_gpkg, driver='GPKG')

