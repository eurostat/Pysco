import numpy as np
import rasterio
import shapely.geometry
import geopandas as gpd

# extent if iceland
xmin, ymin, xmax, ymax = 2300000, 4470000, 3890000, 5440000

# load iceland land area geometre from geopackage
land_geometry = gpd.read_file('/home/juju/gisco/census_2021_iceland/land_100k.gpkg')
land_geometry = land_geometry.geometry.iloc[0]
#print(land_geometry)

output_cells = []
for x in range(xmin, xmax, 1000):
    for y in range(ymin, ymax, 1000):
        cell = shapely.geometry.box(x, y, x + 1000, y + 1000)
        if not land_geometry.intersects(cell): continue

        intersection = land_geometry.intersection(cell)
        if intersection.area <= 0: continue

        print(f'Cell at ({x}, {y}) intersects land area with geometry: {intersection.area}')
        output_cells.append( { "geometry": intersection, "area":intersection.area } )
# save output cells to geopackage
output_gdf = gpd.GeoDataFrame(output_cells, geometry='geometry', crs='EPSG:3035')
output_gdf.to_file('/home/juju/gisco/census_2021_iceland/land_1km_cells.gpkg', driver='GPKG')



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



