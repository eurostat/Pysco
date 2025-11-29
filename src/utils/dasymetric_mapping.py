import numpy as np
import geopandas as gpd
import shapely.geometry
from rtree import index
import random


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
    # simple polygon case
    if isinstance(geometry, geometry.Polygon): return geometry.convex_hull.centroid
    # multipolygon case
    poly = max(list(geometry.geoms), key=lambda p: p.area)
    return poly.convex_hull.centroid


def stats_to_synthetic_population(stats, nb, pop_structure, check_counts=False):
    """ Make a synthetic population of nn persons

    Args:
        stats (): Data on the population distribution by group
        nb (int): Number or persons in the population
        pop_structure (dict): population structure. Example: { "sex" : ["sex_1", "sex_2"], "age_g" : ["age_g_1","age_g_2","age_g_3"], "pob_l" : ["pob_l_1","pob_l_2_1","pob_l_2_2"], "roy" : ["roy_1","roy_2_1","roy_2_2"] }
        check_counts (bool, optional): Check if the sum of the categories equals to the total population. Defaults to False.

    Returns:
        Array: An array of nb persons.
    """

    # build lists of values
    lists = {}
    for key, labels in pop_structure.items():
        result = []
        for label in labels: result.extend([label] * stats.get(label, 0))
        lists[key] = result

    #
    categories = pop_structure.keys()

    # check totals
    if check_counts:
        for cat in categories:
            if len(lists[cat]) != nb:
                #print(data)
                print("Counts in data do not sum to n", cat, len(lists[cat]), nb)

    # shuffle
    for cat in categories:
        random.shuffle(lists[cat])

    # make population
    population = []
    for i in range(nb):

        # make person
        person = {}

        # fill categories
        for cat in categories:
            if i>=len(lists[cat]): person[cat] = None
            else: person[cat] = lists[cat][i]

        # add to population
        population.append(person)

    return population


def synthetic_population_to_stats(population, categories=[], tot_pop_att=None, sort=True):
    """
    population : population of people
    categories     : list of category names to count
    tot_pop_att : The total population attribute

    Returns a dictionary: { field_name: count }
    """

    stats = {}
    for person in population:
        for cat in categories:
            mode = person.get(cat)
            if mode is None: continue
            if mode in stats: stats[mode] = stats[mode] + 1
            else: stats[mode] = 1

    # sort
    if sort: stats = { k: stats[k] for k in sorted(stats) }

    # store population
    if tot_pop_att is not None: stats[tot_pop_att] = len(population)
    return stats




def dasymetric_disaggregation_step_1(input_pop_gpkg,
                                     input_dasymetric_gpkg = None,
                                     output_gpkg = None,
                                     output_synthetic_population_gpkg = None,
                                     tot_pop_att = "TOT_POP",
                                     pop_structure = {},
                                     pop_grouping_threshold = 6):
    """ Disaggregate population units to either dasymetric areas or optionally generate synthetic population or both.

    Args:
        input_pop_gpkg (_type_): The input statistical units, with population figures.
        input_dasymetric_gpkg (_type_): The input dasymetric features, that is those used to distribute the population over.
        output_gpkg (_type_): The output dasymetric features, with population figures attached to it.
        output_synthetic_population_gpkg (_type_, optional): _description_. Defaults to None. The output synthetic population.
        tot_pop_att (str, optional): _description_. Defaults to "TOT_POP". The total population attribute name, in the input_pop_gpkg file.
        pop_structure (dict, optional): _description_. Defaults to {}. A dictionnary describing the population structure, by categories.
        pop_grouping_threshold (int, optional): _description_. Defaults to 6. For synthetic population, the synthetic people belonging to a unit with a population below this threshol are distributed at the same location - a being located at the same place.
    """

    if input_dasymetric_gpkg is not None:
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
    for _, punit in gdf.iterrows():

        # get unit population and geometry
        tot_pop = int(punit[tot_pop_att])
        if tot_pop is None or tot_pop <= 0: continue
        g = punit.geometry

        if das_index is not None:

            # get dasymetric indexes using spatial index
            das_i = list(das_index.intersection(g.bounds))

            # make list of dasymetric geometries
            das_g = []
            for id in das_i: das_g.append(gdf_dasymetric[id])
            das_i = None

            # make union
            das_g = shapely.ops.unary_union(das_g)
    
            # compute intersection
            inter = g.intersection(das_g)

            if inter.area <= 0:
                #print('No dasymetric area found for unit with population:', pop, "around point", g.representative_point())
                # use entire origin geometry
                inter = g
            g = inter

        if output_gpkg is not None:

            # output areas
            f = { "geometry": g, tot_pop_att: tot_pop }

            # copy attributes
            for atts in pop_structure.values():
                for att in atts: f[att] = punit.get(att)

            output_areas.append(f)

        # generate synthetic population within geometry
        if output_synthetic_population_gpkg is not None:

            # make synthetic population
            sp = stats_to_synthetic_population(punit, tot_pop, pop_structure, check_counts=False)

            # move persons to random locations
            if pop_grouping_threshold is not None and tot_pop <= pop_grouping_threshold:
                # small population, put all at the centroid
                # pt = g.representative_point()
                pt = centroid_of_largest_hull(g)
                for i in range(tot_pop): sp[i]['geometry'] = pt
            else:
                # make random locations within geometry
                points = random_points_within(g, tot_pop)

                # put localisation to each person
                for i in range(tot_pop): sp[i]['geometry'] = points[i]
            #
            output_synthetic_population.extend(sp)

    # save output areas
    if output_gpkg is not None:
        gpd.GeoDataFrame(output_areas, geometry='geometry', crs=gdf.crs).to_file(output_gpkg, driver='GPKG')

    if output_synthetic_population_gpkg is not None:
        # save output points
        gpd.GeoDataFrame(output_synthetic_population, geometry='geometry', crs=gdf.crs).to_file(output_synthetic_population_gpkg, driver='GPKG')



def dasymetric_aggregation_step_2(input_das_gpkg,
                                  output_gpkg,
                                  tot_pop_att = "TOT_POP",
                                  pop_structure = {},
                                  type= 'area',
                                  resolution= 1000):
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
                stats = synthetic_population_to_stats(population, categories=pop_structure.keys(), tot_pop_att=tot_pop_att, sort=True)

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

