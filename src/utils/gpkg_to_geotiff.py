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
    bbox=None,
    attributes=None,
    grid_id_field='GRD_ID',
    nodata_value=-9999
):
    """
    Convert vector grid cells from one or several GeoPackage files into a multi-band GeoTIFF.

    Parameters:
    - input_gpkgs (list of str): List of input GeoPackage file paths.
    - output_tiff (str): Output GeoTIFF file path.
    - grid_id_field (str): Name of the grid cell ID field. Defaults to 'GRD_ID'.
    - attributes (list of str): Attributes to export into GeoTIFF bands. If None, all attributes except the grid ID are used.
    - nodata_value (numeric): Nodata value for empty pixels. Default is -9999.
    """

    resolution = None
    with fiona.open(input_gpkgs[0]) as src:
        for f in src:
            id = f['properties'][grid_id_field]
            id = id.split("RES")[1]
            id = id.split("m")[0]
            resolution = int(id)
            break
    print(f"Grid resolution: {resolution}")

    if bbox is None:
        minx = None; miny = None; maxx = None; maxy = None
        for gpkg in input_gpkgs:
            with fiona.open(gpkg) as src:
                (x,y,x_,y_) = src.bounds
                if minx is None or x<minx: minx = x
                if miny is None or y<miny: miny = y
                if maxx is None or x_<maxx: maxx = x_
                if maxy is None or y_<maxy: maxy = y_
        bbox = [minx-resolution, miny-resolution, maxx+resolution, maxy+resolution]
        print(f"Extent: {bbox}")


    # Determine attributes to export
    if attributes is None:
        with fiona.open(input_gpkgs[0]) as src:
            for f in src:
                attributes = [key for key in f['properties'].keys() if key != grid_id_field]
                break
        print(f"Attributes to export: {attributes}")

    # Compute raster dimensions
    [minx, miny, maxx, maxy] = bbox
    width = int(ceil((maxx - minx) / resolution))
    height = int(ceil((maxy - miny) / resolution))

    print(f"Raster size: {width} x {height} cells")

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

            for f in src:
                p = f['properties']
                id = p[grid_id_field]
                #CRS3035RES100mN2361200E3848300
                id = id.split("N")[1].split("E")
                x = int(id[1])
                y = int(id[0])

                col = int((x - minx) / resolution)
                row = int((maxy - y) / resolution)-1

                #print(x,y,col,row)

                for a in attributes:
                    value = p.get(a)
                    if value is not None:
                        band_arrays[a][row, col] = value

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
        transform=from_origin(minx, maxy, resolution, resolution),
        nodata=nodata_value
    ) as dst:
        for idx, attr in enumerate(attributes, start=1):
            dst.write(band_arrays[attr], idx)
            dst.set_band_description(idx, attr)



# for testing
gpkg_grid_to_geotiff(
        [
            "/home/juju/gisco/accessibility/out_partition_education/euroaccess_education_100m_2500000_3500000.gpkg"
            #"/home/juju/gisco/accessibility/out_partition_education/euroaccess_education_100m_2500000_2000000.gpkg"
            #"/home/juju/gisco/accessibility/out_partition_education/euroaccess_education_100m_2500000_1500000.gpkg"
        ],
        "/home/juju/gisco/accessibility/test.tif",
        attributes=["duration_1", "duration_average_3", "distance_to_node"],
)

