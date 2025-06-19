from math import ceil, floor
import rasterio
from rasterio.transform import from_bounds, Affine, from_origin
from rasterio.windows import from_bounds as window_from_bounds
from rasterio.enums import Resampling
from rasterio.features import rasterize
import numpy as np
import os
import fiona
import geopandas as gpd
from shapely.geometry import shape




def rasterise_tesselation_gpkg(
    input_gpkg,
    output_tiff,
    layer=None,
    fieldname='code',
    resolution=1000,
    compression='none',
    nodata_value=-9999,
    bbox=None,
    dtype=np.float32,
    all_touched=False
):
    # Open vector file
    with fiona.open(input_gpkg, layer=layer) as src:
        crs = src.crs
        bounds = src.bounds if bbox is None else bbox

        # ensure bounds are resolution-rounded
        minx = floor(bounds[0]/resolution)*resolution
        miny = floor(bounds[1]/resolution)*resolution
        maxx = ceil(bounds[2]/resolution)*resolution
        maxy = ceil(bounds[3]/resolution)*resolution

        # Compute raster dimensions
        width = int((maxx - minx) / resolution)
        height = int((maxy - miny) / resolution)

        # Prepare shapes with value tuples for rasterisation
        shapes = (
            (shape(feature['geometry']), feature['properties'][fieldname])
            for feature in src
        )

        # Define raster transform
        transform = rasterio.transform.from_origin(minx, maxy, resolution, resolution)

        # Rasterise
        raster = rasterize(
            shapes=shapes,
            out_shape=(height, width),
            fill=nodata_value,
            transform=transform,
            dtype=dtype,
            all_touched=all_touched
        )

    # Define raster profile
    profile = {
        'driver': 'GTiff',
        'height': height,
        'width': width,
        'count': 1,
        'dtype': dtype,
        'crs': crs,
        'transform': transform,
        'nodata': nodata_value,
        'compress': compression
    }

    # Write output raster
    with rasterio.open(output_tiff, 'w', **profile) as dst:
        dst.write(raster, 1)

    print(f"Raster saved to {output_tiff}")







def rename_geotiff_bands(input_path, new_band_names, output_path=None):
    """
    Rename the bands (descriptions) of a GeoTIFF file.
    
    Parameters:
        input_path (str): Path to the input GeoTIFF file.
        new_band_names (list of str): List of new band names.
        output_path (str): Path to save the modified GeoTIFF.
    """
    with rasterio.open(input_path) as src:
        if len(new_band_names) != src.count:
            raise ValueError(f"Number of new band names ({len(new_band_names)}) "
                             f"must match number of bands in the file ({src.count}).")

        profile = src.profile

        # Copy data to a new file with updated descriptions
        if output_path is None: output_path = input_path
        with rasterio.open(output_path, 'w', **profile) as dst:
            for i in range(1, src.count + 1):
                data = src.read(i)
                dst.write(data, i)
                dst.set_band_description(i, new_band_names[i - 1])



def combine_geotiffs(input_files, output_file, nodata_value=None, compress=None, dtype=None):
    """
    Combine multiple GeoTIFF files (single or multi-band) into a single multi-band GeoTIFF.
    Assumes same CRS, resolution, and aligned grids.
    Converts to specified dtype if provided.

    Parameters:
    - input_files: list of input GeoTIFF file paths.
    - output_file: path for the output GeoTIFF file.
    - nodata_value: optional value to use in the output GeoTIFF file for areas without data.
    - compress: optional compression method (e.g. 'LZW').
    - dtype: optional output data type (e.g. 'float32', 'int16'). If None, use first input file dtype.
    """

    datasets = [rasterio.open(f) for f in input_files]

    # Validate matching CRS, resolution
    crs = datasets[0].crs
    res = datasets[0].res

    for ds in datasets:
        if ds.crs != crs:
            raise ValueError("All input GeoTIFFs must have same CRS.")
        if ds.res != res:
            raise ValueError("All input GeoTIFFs must have same resolution.")

    # Check and resolve data types
    input_dtypes = set(ds.dtypes[0] for ds in datasets)

    if dtype is None:
        if len(input_dtypes) > 1:
            raise ValueError(f"Input files have different data types: {input_dtypes}. Specify a 'dtype' to convert.")
        dtype = datasets[0].dtypes[0]

    # Check and resolve nodata
    input_nodatas = set(ds.nodata for ds in datasets)

    if nodata_value is None:
        if len(input_nodatas) > 1:
            raise ValueError(f"Input files have different nodata: {input_nodatas}. Specify a 'nodata' to convert.")
        nodata_value = datasets[0].nodata

    # Compute combined bounds
    minxs, minys, maxxs, maxys = zip(*[ds.bounds for ds in datasets])
    output_bounds = (min(minxs), min(minys), max(maxxs), max(maxys))

    # Calculate output shape and transform
    width = int(np.ceil((output_bounds[2] - output_bounds[0]) / res[0]))
    height = int(np.ceil((output_bounds[3] - output_bounds[1]) / res[1]))
    transform = from_bounds(*output_bounds, width, height)

    # Total output band count
    total_bands = sum(ds.count for ds in datasets)

    # Prepare metadata
    out_meta = {
        'driver': 'GTiff',
        'height': height,
        'width': width,
        'count': total_bands,
        'crs': crs,
        'transform': transform,
        'dtype': dtype,
        'nodata': nodata_value
    }
    if compress:
        out_meta['compress'] = compress

    # Create output file and write data
    with rasterio.open(output_file, 'w', **out_meta) as dest:
        band_index = 1
        for ds in datasets:
            # Compute window in output raster for this input raster
            window = window_from_bounds(*ds.bounds, transform=transform)

            row_off, col_off = int(window.row_off), int(window.col_off)
            rows, cols = ds.height, ds.width

            for i in range(ds.count):
                # Read data for this band
                data = ds.read(i+1)

                # Convert to desired dtype if necessary
                if data.dtype != dtype:
                    data = data.astype(dtype)

                # Use common nodata value, for all bands
                if ds.nodata != nodata_value:
                    data[data == ds.nodata] = nodata_value

                # Create full-size array filled with nodata
                full_data = np.full((height, width), nodata_value, dtype=dtype)

                # Place input data into correct window
                full_data[row_off:row_off+rows, col_off:col_off+cols] = data

                # Write to corresponding band in output
                dest.write(full_data, band_index)

                # Set band description
                desc = ds.descriptions[i]
                if not desc:
                    desc = f"{os.path.basename(ds.name)}_band{i+1}"
                dest.set_band_description(band_index, desc)

                band_index += 1

    # Close all input datasets
    for ds in datasets:
        ds.close()




# apply mask on a geotiff based on some geometries from a vector file
def geotiff_mask_by_countries(
            in_tiff_path,
            out_tiff_path,
            gpkg,
            gpkg_column,
            values, # the ones to keep
            compress=None,
            all_touched=True
    ):
    # read input raster
    with rasterio.open(in_tiff_path) as src:
        profile = src.profile.copy()
        data = src.read()
        transform = src.transform
        crs = src.crs
        height, width = src.height, src.width

    # get geometries for masking
    gdf = gpd.read_file(gpkg)
    gdf = gdf[gdf[gpkg_column].isin(values)]

    # projection change, if needed
    if gdf.crs != crs:
        gdf = gdf.to_crs(crs)

    # get nodata value
    nodata_value = profile.get('nodata', None)
    if nodata_value is None:
        nodata_value = -9999
        profile.update(nodata=nodata_value)

    # mask based on pixel square intersection (any overlap)
    mask = rasterize(
        [(geom, 1) for geom in gdf.geometry],
        out_shape=(height, width),
        transform=transform,
        fill=0,  # pixels with no intersection
        all_touched= all_touched,  # any intersection with pixel => burn value
        dtype='uint8'
    ) == 0  # True where no intersection

    # apply mask to every band: set pixels outside geometries to nodata
    data[:, mask] = nodata_value

    # set compression
    if compress is not None:
        profile.update(compress=compress)

    # write output tiff
    with rasterio.open(out_tiff_path, 'w', **profile) as dst:
        dst.write(data)



def add_ratio_band(input_path, numerator_band, denominator_band, ratio_band_name='ratio_band', output_path=None):
    """
    Adds a new band to a GeoTIFF file, containing the ratio of two existing bands multiplied by 100.
    The result is nodata where either input band has nodata or where denominator is 0.

    Parameters:
        input_path (str): Path to input GeoTIFF.
        numerator_band (int): 1-based index of the numerator band.
        denominator_band (int): 1-based index of the denominator band.
        ratio_band_name (str): Description for the new band (optional).
        output_path (str): Path to output GeoTIFF with added ratio band.
    """
    with rasterio.open(input_path) as src:
        meta = src.meta.copy()
        nodata_value = src.nodata

        # Read bands
        num = src.read(numerator_band)
        den = src.read(denominator_band)

        # Compute ratio × 100 with masking
        ratio = np.full_like(num, nodata_value, dtype=src.dtypes[0])

        mask_valid = (num != nodata_value) & (den != nodata_value) & (den != 0)
        ratio[mask_valid] = (num[mask_valid] / den[mask_valid]) * 100

        # Update metadata: increase band count
        meta.update(count=src.count + 1)

        # Write to a new file with all original bands and the new ratio band
        if output_path is None: output_path = input_path
        with rasterio.open(output_path, 'w', **meta) as dst:
            # Copy existing bands
            for i in range(1, src.count + 1):
                data = src.read(i)
                dst.write(data, i)

            # Write ratio band
            dst.write(ratio, src.count + 1)
            dst.update_tags(src.count + 1, BAND_NAME=ratio_band_name)




def resample_geotiff_aligned(input_path, output_path, new_resolution, resampling=Resampling.average, dtype=np.float64):
    """
    Resamples a GeoTIFF to a new resolution (must be a multiple of the original),
    and aligns the origin point to a multiple of the new resolution.

    Parameters:
        input_path (str): Path to the input GeoTIFF file.
        output_path (str): Path to save the resampled GeoTIFF.
        new_resolution (float): Desired resolution (pixel size, e.g. in meters).
        resampling (): Resampling method.
    """
    with rasterio.open(input_path) as src:
        # Original resolution
        original_res_x = src.transform.a
        original_res_y = -src.transform.e

        # Check that new resolution is a multiple of original
        if new_resolution % original_res_x != 0 or new_resolution % original_res_y != 0:
            raise ValueError("New resolution must be a multiple of the original resolution.")

        # Original bounds
        bounds = src.bounds

        # Align the origin to a multiple of new_resolution
        aligned_minx = floor(bounds.left  / new_resolution) * new_resolution
        aligned_maxy = ceil (bounds.top   / new_resolution) * new_resolution
        aligned_maxx = ceil (bounds.right / new_resolution) * new_resolution
        aligned_miny = floor(bounds.bottom/ new_resolution) * new_resolution

        # New dimensions
        new_width  = int((aligned_maxx - aligned_minx) / new_resolution)
        new_height = int((aligned_maxy - aligned_miny) / new_resolution)

        # New transform
        new_transform = Affine(
            new_resolution, 0.0, aligned_minx,
            0.0, -new_resolution, aligned_maxy
        )

        # Update profile
        profile = src.profile
        profile.update({
            'height': new_height,
            'width': new_width,
            'transform': new_transform
        })

        if dtype is not None:
            profile.update({ 'dtype': dtype })


        with rasterio.open(output_path, 'w', **profile) as dst:
            for i in range(1, src.count + 1):
                rasterio.warp.reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=new_transform,
                    dst_crs=src.crs,
                    resampling=resampling,
                    dtype=dtype
                )




def extend_crop_bounding_box(input_path, new_bbox, output_path):
    """
    Create a new GeoTIFF with a new bounding box, filling extra areas with nodata.

    Parameters:
        input_path (str): Path to the input GeoTIFF.
        new_bbox (tuple): New bounding box as (minx, miny, maxx, maxy).
        output_path (str): Path to save the output GeoTIFF.
    """
    with rasterio.open(input_path) as src:
        old_transform = src.transform
        pixel_width, pixel_height = old_transform.a, -old_transform.e
        nodata = src.nodata if src.nodata is not None else np.nan

        # Compute new raster dimensions
        new_minx, new_miny, new_maxx, new_maxy = new_bbox
        new_width = int(np.ceil((new_maxx - new_minx) / pixel_width))
        new_height = int(np.ceil((new_maxy - new_miny) / pixel_height))

        new_transform = from_origin(new_minx, new_maxy, pixel_width, pixel_height)

        # Prepare output metadata
        out_meta = src.meta.copy()
        out_meta.update({
            "height": new_height,
            "width": new_width,
            "transform": new_transform,
            "nodata": nodata
        })

        # Create empty output raster
        with rasterio.open(output_path, "w", **out_meta) as dst:
            for i in range(1, src.count + 1):
                # Initialize with nodata
                data = np.full((new_height, new_width), nodata, dtype=src.dtypes[i-1])

                # Compute window intersection between old and new bbox
                window = from_bounds(
                    max(new_minx, src.bounds.left),
                    max(new_miny, src.bounds.bottom),
                    min(new_maxx, src.bounds.right),
                    min(new_maxy, src.bounds.top),
                    transform=src.transform
                ).round_offsets().round_lengths()

                if window.width > 0 and window.height > 0:
                    # Read data from source
                    src_data = src.read(i, window=window)

                    # Compute destination window
                    dest_window = from_bounds(
                        src.xy(window.row_off, window.col_off)[0],
                        src.xy(window.row_off + window.height, window.col_off + window.width)[1],
                        src.xy(window.row_off + window.height, window.col_off + window.width)[0],
                        src.xy(window.row_off, window.col_off + window.width)[1],
                        transform=new_transform
                    ).round_offsets().round_lengths()

                    # Write to appropriate position in destination array
                    data[
                        int(dest_window.row_off):int(dest_window.row_off + dest_window.height),
                        int(dest_window.col_off):int(dest_window.col_off + dest_window.width)
                    ] = src_data

                # Write band to output
                dst.write(data, i)
