import fiona
import rasterio
from shapely.geometry import Polygon,Point
from rasterio.transform import from_origin
import numpy as np
from math import ceil,isnan
from datetime import datetime
import geopandas as gpd
import pandas as pd

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.gridutils import get_cell_xy_from_id


def parquet_grid_to_gpkg(
        input_parquet_files,
        output_gpkg,
        layer_name = None,
        grid_id_field='GRD_ID',
        geometry_type="polygon", #could be "point"
):
# convert a list of parquet grid files into a single GPKG file.
# The cell geometries are built from the grid cell ID.

    first = True
    for input_parquet in input_parquet_files:

        # Load the parquet file
        df = pd.read_parquet(input_parquet)
        if df.size == 0: continue

        # Function to create a square polygon from the cell ID
        def create_square_polygon(s):
            # decode cell ID
            # CRS3035RES100mN2953200E4041600
            s = s.split('RES')[1].split('mN')
            res = int(s[0])
            s = s[1].split('E')
            x = int(s[1])
            y = int(s[0])

            # make polygon
            if geometry_type == "polygon":
                xy = (x, y)
                return Polygon([xy, (x + res, y), (x + res, y + res), (x, y + res), xy])
            if geometry_type == "point":
                return Point((x + res/2, y + res/2))
            print("Unexpected geometry type: " + geometry_type)

        # Apply the function to create a new column with polygons and CRS
        df['geometry'] = df.apply(
            lambda cell: create_square_polygon(cell[grid_id_field]),
            axis=1
        )

        # get CRS
        crs = df.iloc[0][grid_id_field]
        crs = crs.split('RES')
        crs = crs[0][3:]

        # Make GeoDataFrame
        df = gpd.GeoDataFrame(df, geometry='geometry')

        # Set the CRS
        df.set_crs(epsg=crs, inplace=True)

        # save to GPKG
        if first:
            df.to_file(output_gpkg, layer=layer_name, driver="GPKG")
            first = False
        else:
            df.to_file(output_gpkg, layer=layer_name, driver="GPKG", mode='a')




def parquet_grid_to_geotiff(
    input_parquet_files,
    output_tiff,
    grid_id_field='GRD_ID',
    attributes=None,
    bbox=None,
    parquet_nodata_values=None,
    tiff_nodata_value=-9999,
    dtype=np.int16,
    value_fun=None,
    compress='none'
):
    """
    Convert vector grid cells from one or several parquet grid files into a multi-band GeoTIFF.

    Parameters:
    - input_parquets (list of str): List of input parquet grid file paths.
    - output_tiff (str): Output GeoTIFF file path.
    - grid_id_field (str): Name of the grid cell ID field. Defaults to 'GRD_ID'.
    - attributes (list of str): Attributes to export into GeoTIFF bands. If None, all attributes except the grid ID are used.
    - bbox: Bounding box [minx, miny, maxx, maxy] to take. If not specified, the GPKG files bbox is computed and used - in that case, it is assumed the grid cell geometries are polygons.
    - parquet_nodata_values (list of numbers): If specified, the parquet file attributes with these values will be encoded as nodata in the tiff. Default is None.
    - tiff_nodata_value (numeric): Nodata value for empty pixels. Default is -9999.
    - value_fun (function): A function that take a value and return another one. If specified, it is applied to the parquet values after being read. It may be used for example to change the parquet values.
    - compress (str): Tiff compression, among 'lzw','deflate','jpeg','packbits','none'. Default is none.
    """

    # Determine resolution and CRS
    # It is assumed all cells of all GPKG files have the same resolution and CRS
    resolution = None
    crs = None
    for file in input_parquet_files:

        # Load the parquet file
        df = pd.read_parquet(file)
        if df.size == 0: continue

        id = df.iloc[0][grid_id_field]
        a = id.split('RES')

        # get CRS
        crs = "EPSG:" + a[0][3:]

        # get resolution
        a = a[1]
        a = a.split("m")[0]
        resolution = int(a)

        if attributes is None:
            # Determine attributes to export
            # It is assumed all parquet files have the same structure
            attributes = df.columns.tolist()
            attributes.remove(grid_id_field)

        # no need to continue, assuming all parquet files have the same structure
        break
    print(f"Grid resolution: {resolution}")
    print(f"Grid CRS: {crs}")
    print(f"Attributes to export: {attributes}")

    # Determine the bounding box
    if bbox is None:
        minx = None; miny = None; maxx = None; maxy = None
        for file in input_parquet_files:
            # Load the parquet file
            df = pd.read_parquet(file)
            if df.size == 0: continue

            for cell in df.itertuples(index=True):
                id = getattr(cell, grid_id_field)
                x,y = get_cell_xy_from_id(id)
                x_ = x+resolution
                y_ = y+resolution
                try:
                    if minx is None or x<minx: minx = x
                    if miny is None or y<miny: miny = y
                    if maxx is None or x_>maxx: maxx = x_
                    if maxy is None or y_>maxy: maxy = y_
                except: continue
        bbox = [minx, miny, maxx, maxy]
        print(f"Extent: {bbox}")

    # Compute raster dimensions
    [minx, miny, maxx, maxy] = bbox
    width = ceil((maxx - minx) / resolution)
    height = ceil((maxy - miny) / resolution)

    # Prepare raster bands
    band_arrays = {
        attr: np.full((height, width), tiff_nodata_value, dtype=dtype)
        for attr in attributes
    }

    print("Populate raster bands")

    nb = len(input_parquet_files)
    i=1
    for file in input_parquet_files:

        # Load the parquet file
        df = pd.read_parquet(file)

        print(datetime.now(), i, "/", nb, df.size, "cells", file)
        i += 1

        if df.size == 0: continue

        for cell in df.itertuples(index=True):
            id = getattr(cell, grid_id_field)
            #CRS3035RES100mN2361200E3848300

            # get cell lower left coordinates
            x,y = get_cell_xy_from_id(id)
            #TODO also check all cells have the same RES ?

            # get pixel position
            col = int((x - minx) / resolution)
            row = int((maxy - y) / resolution)-1

            if col <0 or col > width: continue
            if row <0 or row > height: continue

            # set raster values at pixel position
            for a in attributes:
                value = getattr(cell, a)
                if value_fun: value = value_fun(value)
                if value is None: continue
                if isnan(value): continue
                if parquet_nodata_values is not None and value in parquet_nodata_values: continue
                band_arrays[a][row, col] = value

    # Write to GeoTIFF
    print(datetime.now(), f"Writing GeoTIFF to {output_tiff}")
    with rasterio.open(
        output_tiff,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=len(attributes),
        dtype=dtype,
        crs=crs,
        transform=from_origin(minx, maxy, resolution, resolution),
        nodata=tiff_nodata_value,
        compress='none' if compress is None else compress
    ) as dst:
        for idx, attr in enumerate(attributes, start=1):
            dst.write(band_arrays[attr], idx)
            dst.set_band_description(idx, attr)






def gpkg_grid_to_geotiff(
    input_gpkgs,
    output_tiff,
    grid_id_field='GRD_ID',
    attributes=None,
    bbox=None,
    gpkg_nodata_values=None,
    tiff_nodata_value=-9999,
    dtype=np.int16,
    compress='none'
):
    """
    Convert vector grid cells from one or several GeoPackage files into a multi-band GeoTIFF.

    Parameters:
    - input_gpkgs (list of str): List of input GeoPackage file paths.
    - output_tiff (str): Output GeoTIFF file path.
    - grid_id_field (str): Name of the grid cell ID field. Defaults to 'GRD_ID'.
    - attributes (list of str): Attributes to export into GeoTIFF bands. If None, all attributes except the grid ID are used.
    - bbox: Bounding box [minx, miny, maxx, maxy] to take. If not specified, the GPKG files bbox is computed and used - in that case, it is assumed the grid cell geometries are polygons.
    - gpkg_nodata_values (list of numbers): If specified, the GPKG file attributes with these values will be encoded as nodata in the tiff. Default is None.
    - tiff_nodata_value (numeric): Nodata value for empty pixels. Default is -9999.
    - compress (str): Tiff compression, among 'lzw','deflate','jpeg','packbits','none'. Default is none.
    """



    # Determine resolution
    # It is assumed all cells of all GPKG files have the same resolution
    resolution = None
    for gpkg in input_gpkgs:
        with fiona.open(gpkg) as src:
            for f in src:
                id = f['properties'][grid_id_field]
                id = id.split("RES")[1]
                id = id.split("m")[0]
                resolution = int(id)
                break
        if resolution is not None: break
    print(f"Grid resolution: {resolution}")

    # Determine attributes to export
    # It is assumed all GPKG files have the same structure
    if attributes is None:
        for gpkg in input_gpkgs:
            with fiona.open(gpkg) as src:
                for f in src:
                    attributes = [key for key in f['properties'].keys() if key != grid_id_field]
                    break
            if attributes is not None: break
        print(f"Attributes to export: {attributes}")

    # Determine the bounding box
    # here it is assumed the grid cells have a geometry and it is a polygon.
    # This may be based on the grid_id but it would require checking all cell ids individually and thus take long.
    if bbox is None:
        minx = None; miny = None; maxx = None; maxy = None
        for gpkg in input_gpkgs:
            with fiona.open(gpkg) as src:
                try:
                    (x,y,x_,y_) = src.bounds
                    if minx is None or x<minx: minx = x
                    if miny is None or y<miny: miny = y
                    if maxx is None or x_>maxx: maxx = x_
                    if maxy is None or y_>maxy: maxy = y_
                except: pass
        bbox = [minx, miny, maxx, maxy]
        print(f"Extent: {bbox}")

    # Compute raster dimensions
    [minx, miny, maxx, maxy] = bbox
    width = ceil((maxx - minx) / resolution)
    height = ceil((maxy - miny) / resolution)

    print(f"Raster size: {width} x {height} cells")

    # Prepare raster bands
    band_arrays = {
        attr: np.full((height, width), tiff_nodata_value, dtype=dtype)
        for attr in attributes
    }

    print("Populating raster bands...")

    crs = None
    for gpkg in input_gpkgs:
        print(datetime.now(), gpkg)
        with fiona.open(gpkg) as src:

            # retrieve CRS
            if crs is None: crs = src.crs

            for f in src:
                p = f['properties']
                id = p[grid_id_field]
                #CRS3035RES100mN2361200E3848300

                # get cell lower left coordinates
                x,y = get_cell_xy_from_id(id)
                #TODO also check all cells have the same RES ?

                # get pixel position
                col = int((x - minx) / resolution)
                row = int((maxy - y) / resolution)-1

                if col <0 or col > width: continue
                if row <0 or row > height: continue

                # set raster values at pixel position
                for a in attributes:
                    value = p.get(a)
                    if value is None: continue
                    if gpkg_nodata_values is not None and value in gpkg_nodata_values: continue
                    band_arrays[a][row, col] = value

    # Write to GeoTIFF
    print(datetime.now(), f"Writing GeoTIFF to {output_tiff}")
    with rasterio.open(
        output_tiff,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=len(attributes),
        dtype=dtype,
        crs=crs,
        transform=from_origin(minx, maxy, resolution, resolution),
        nodata=tiff_nodata_value,
        compress='none' if compress is None else compress
    ) as dst:
        for idx, attr in enumerate(attributes, start=1):
            dst.write(band_arrays[attr], idx)
            dst.set_band_description(idx, attr)



'''
# for testing
gpkg_grid_to_geotiff(
        [
            #"/home/juju/gisco/accessibility/out_partition_education/euroaccess_education_100m_2500000_3500000.gpkg",
            "/home/juju/gisco/accessibility/out_partition_education/euroaccess_education_100m_2500000_2000000.gpkg",
            "/home/juju/gisco/accessibility/out_partition_education/euroaccess_education_100m_2500000_1500000.gpkg",
        ],
        "/home/juju/gisco/accessibility/test.tif",
        attributes=["duration_1", "duration_average_3", "distance_to_node"],
        gpkg_nodata_values=[-1],
        compress='deflate'
)

'''