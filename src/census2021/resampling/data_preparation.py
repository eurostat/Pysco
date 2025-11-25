import geopandas as gpd
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape
import pandas as pd

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.convert import parquet_grid_to_gpkg



def raster_pixels_above_threshold_to_gpkg(tiff_paths, threshold, output_gpkg, layer_name=None):
    """
    Extracts pixels > threshold from one or more GeoTIFF rasters and
    saves each pixel as a polygon feature in a GeoPackage.

    Parameters
    ----------
    tiff_paths : list of str
        List of paths to GeoTIFF files.
    threshold : float
        Pixel threshold value.
    output_gpkg : str
        Path of output GeoPackage to create.
    layer_name : str
        Name of layer inside GPKG.
    """

    all_geoms = []
    all_vals = []

    for path in tiff_paths:
        with rasterio.open(path) as src:
            data = src.read(1)
            mask = data >= threshold

            # shapes() yields (geometry, value) pairs
            for geom, val in shapes(data, mask=mask, transform=src.transform):
                all_geoms.append(shape(geom))
                all_vals.append(float(val))

    # Write to GeoPackage
    gpd.GeoDataFrame( {"value": all_vals}, geometry=all_geoms, crs=src.crs).to_file(output_gpkg, layer=layer_name, driver="GPKG")




w = '/home/juju/gisco/census_2021_iceland/'

# GHSL to vector
'''
raster_pixels_above_threshold_to_gpkg(
    ['/home/juju/geodata/IS/GHS_BUILT_S_E2020_GLOBE_R2023A_54009_100_V1_0_R2_C17.tif', '/home/juju/geodata/IS/GHS_BUILT_S_E2020_GLOBE_R2023A_54009_100_V1_0_R2_C18.tif'],
    1, w+'out/ghsl.gpkg')
'''


'''
# restructure IS CSV file
df = pd.read_csv(w+'ice_grid_cells.csv', sep=";")
def myfunc(id): return "CRS3057RES" + id.replace("1km", "1000m").replace("E", "000E") + "000"

# 3. Apply the function to a column
df["GRD_ID"] = df["ice_cell_name"].apply(myfunc)
df = df.drop(columns=["id", "ice_cell_name"])

# 4. Save back to CSV
df.to_csv(w+'ice_grid_cells_2.csv', index=False)
'''

# CSV to parquet to GPKG
pd.read_csv(w+'ice_grid_cells_2.csv').to_parquet(w+'ice_grid_cells_2.parquet')

#parquet_grid_to_gpkg(w+'ice_grid_cells_2.parquet', w+'IS_pop_grid_surf.gpkg', geometry_type="polygon")
#parquet_grid_to_gpkg(w+'ice_grid_cells_2.parquet', w+'IS_pop_grid_point.gpkg', geometry_type="point")

