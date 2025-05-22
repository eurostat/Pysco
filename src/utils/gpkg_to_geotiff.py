import fiona
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import shape, box
import numpy as np
#import os
#from collections import defaultdict

def gpkg_grid_to_geotiff(
    input_gpkgs,
    output_tiff,
    grid_id_field='GRD_ID',
    attributes=None,
    extent=None,
    nodata_value=-9999
):
    """
    Convert vector grid cells from one or several GeoPackage files into a multi-band GeoTIFF.

    Parameters:
    - input_gpkgs (list of str): List of input GeoPackage file paths.
    - output_tiff (str): Output GeoTIFF file path.
    - grid_id_field (str): Name of the grid cell ID field. Defaults to 'GRD_ID'.
    - attributes (list of str): Attributes to export into GeoTIFF bands. If None, all attributes except the grid ID are used.
    - extent (tuple): Optional geographical extent (minx, miny, maxx, maxy). If None, computed from all gpkg files.
    - nodata_value (numeric): Nodata value for empty pixels. Default is -9999.
    """

    print("Collecting features and computing grid layout...")

    # Collect all features and metadata
    all_features = []
    crs = None
    cell_width = cell_height = None
    all_bounds = []

    for gpkg in input_gpkgs:
        with fiona.open(gpkg) as src:
            if crs is None:
                crs = src.crs
            elif crs != src.crs:
                raise ValueError("All input GeoPackages must have the same CRS.")

            for feat in src:
                geom = shape(feat['geometry'])
                props = feat['properties']

                if cell_width is None:
                    bounds = geom.bounds
                    cell_width = bounds[2] - bounds[0]
                    cell_height = bounds[3] - bounds[1]

                all_features.append((geom, props))
                all_bounds.append(geom.bounds)

    if not all_features:
        raise ValueError("No features found in the provided GeoPackage files.")

    # Determine attributes to export
    if attributes is None:
        attributes = [key for key in all_features[0][1].keys() if key != grid_id_field]

    print(f"Attributes to export: {attributes}")

    # Compute raster extent
    if extent is None:
        minxs, minys, maxxs, maxys = zip(*all_bounds)
        extent = (min(minxs), min(minys), max(maxxs), max(maxys))

    print(f"Raster extent: {extent}")

    # Compute raster dimensions
    minx, miny, maxx, maxy = extent
    width = int(round((maxx - minx) / cell_width))
    height = int(round((maxy - miny) / cell_height))

    print(f"Raster size: {width} x {height} cells")

    # Define transform
    transform = from_origin(minx, maxy, cell_width, cell_height)

    # Prepare raster bands
    band_arrays = {
        attr: np.full((height, width), nodata_value, dtype=np.float32)
        for attr in attributes
    }

    print("Populating raster bands...")

    # Populate raster bands
    for geom, props in all_features:
        col = int((geom.bounds[0] - minx) / cell_width)
        row = int((maxy - geom.bounds[1]) / cell_height)

        for attr in attributes:
            value = props.get(attr)
            if value is not None:
                band_arrays[attr][row, col] = value

    # Write to GeoTIFF
    print(f"Writing GeoTIFF to {output_tiff}")

    with rasterio.open(
        output_tiff,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=len(attributes),
        dtype=np.float32,
        crs=crs,
        transform=transform,
        nodata=nodata_value
    ) as dst:
        for idx, attr in enumerate(attributes, start=1):
            dst.write(band_arrays[attr], idx)
            dst.set_band_description(idx, attr)




gpkg_grid_to_geotiff(
        [
            "/home/juju/gisco/accessibility/out_partition_education/euroaccess_education_100m_4500000_5000000.gpkg",
            "/home/juju/gisco/accessibility/out_partition_education/euroaccess_education_100m_4500000_4500000.gpkg"
        ],
        "/home/juju/gisco/accessibility/test.tif"
)

