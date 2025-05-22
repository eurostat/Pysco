import fiona
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import shape, box
import numpy as np
from math import ceil
#import os
#from collections import defaultdict

def gpkg_grid_to_geotiff(
    input_gpkgs,
    output_tiff,
    resolution=None,
    bbox=None,
    attributes=None,
    grid_id_field='GRD_ID',
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

    if bbox is None:
        print("Get gpkg bbox")
        #TODO get bbox of each file. merge bboxes.
        print(f"Bbox: {bbox}")

    if resolution is None:
        print("Get grid resolution")
        #TODO get first file, first cell id and get resolution from it
        print(f"Grid resolution: {resolution}")

    # Determine attributes to export
    if attributes is None:
        print("Get attributes")
        #TODO get attributes from first cell
        #attributes = [key for key in all_features[0][1].keys() if key != grid_id_field]
        print(f"Attributes to export: {attributes}")


    print("Collecting features and computing grid layout...")

    # Compute raster dimensions
    [minx, miny, maxx, maxy] = bbox
    width = int(ceil((maxx - minx) / resolution))
    height = int(ceil((maxy - miny) / resolution))

    print(f"Raster size: {width} x {height} cells")

    # Define transform
    transform = from_origin(minx, maxy, resolution, resolution)

    # Prepare raster bands
    band_arrays = {
        attr: np.full((height, width), nodata_value, dtype=np.float32)
        for attr in attributes
    }

    print("Populating raster bands...")

    crs = None
    for gpkg in input_gpkgs:
        with fiona.open(gpkg) as src:
            if crs is None:
                crs = src.crs
            elif crs != src.crs:
                raise ValueError("All input GeoPackages must have the same CRS.")

            for feat in src:
                #TODO get position from cell ID intead of geometry.
                geom = shape(feat['geometry'])
                props = feat['properties']

                col = int((geom.bounds[0] - minx) / resolution)
                row = int((maxy - geom.bounds[1]) / resolution)

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
            "/home/juju/gisco/accessibility/out_partition_healthcare/euroaccess_healthcare_100m_2500000_3000000.gpkg"
        ],
        "/home/juju/gisco/accessibility/test.tif"
)

