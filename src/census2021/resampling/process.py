import numpy as np
import rasterio
import shapely.geometry
import geopandas as gpd
from rtree import index


workspace = '/home/juju/gisco/census_2021_iceland/'

# extent if iceland
xmin, ymin, xmax, ymax = 2600000, 4700000, 3400000, 5300000

# load iceland land area geometries from geopackage
land_geometry = gpd.read_file(workspace + 'land_100k_decomposed.gpkg')
land_geometry = land_geometry.geometry
# build spatial index
lg_index = index.Index()
for i,g in enumerate(land_geometry): lg_index.insert(i, g.bounds)



output_cells = []
for x in range(xmin, xmax, 1000):
    print(xmin, x,xmax)
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
    while len(points) < n:
        random_point = shapely.geometry.Point(
            np.random.uniform(minx, maxx),
            np.random.uniform(miny, maxy)
        )
        if geometry.contains(random_point):
            points.append(random_point)
    return points






# load a csv file containing grid data
def load_csv_grid_data(csv_path):
    'Load grid data from a CSV file and return as a numpy array.'
    data = np.genfromtxt(csv_path, delimiter=',', skip_header=1)
    return data

# with a column representing the INSPIRE ID



# and convert it into a list of features with an area geometry in shapely representing the cell squared geometry.




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



