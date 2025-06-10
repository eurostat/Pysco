from math import ceil, floor
import rasterio
import geopandas as gpd
from rasterio.transform import from_bounds
from rasterio.windows import from_bounds as window_from_bounds
import numpy as np
import os
from rasterio.features import rasterize
import fiona
from shapely.geometry import shape
import numpy as np




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



def combine_geotiffs(input_files, output_file, nodata_value=-9999, compress=None, dtype=None):
    """
    Combine multiple GeoTIFF files (single or multi-band) into a single multi-band GeoTIFF.
    Assumes same CRS, resolution, and aligned grids.
    Converts to specified dtype if provided.

    Parameters:
    - input_files: list of input GeoTIFF file paths.
    - output_file: path for the output GeoTIFF file.
    - nodata_value: value for areas without data.
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
          values,
          compress=None,
          centre=True,
          operation = "include", # include or exclude
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
        all_touched= not centre,  # any intersection with pixel => burn value
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

