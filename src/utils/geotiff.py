import rasterio
from rasterio.features import geometry_mask
import geopandas as gpd
from rasterio.transform import from_bounds
from rasterio.enums import Resampling
import numpy as np
from scipy import ndimage
from skimage.morphology import disk
import os

def circular_kernel_sum(
    input_tiff,
    output_tiff,
    radius_m=120000,
    dtype=rasterio.float32,
    compress=None,
):
    with rasterio.open(input_tiff) as src:
        data = src.read(1)
        profile = src.profile
        nodata = src.nodata
        pixel_size, pixel_size_y = src.res
        assert pixel_size == pixel_size_y, "Pixels must be square."

    if nodata is not None:
        data = np.where((data == nodata) | (data < 0), 0, data)
    else:
        data = np.clip(data, 0, None)

    data = data.astype(dtype)

    radius_px = int(radius_m / pixel_size)
    kernel = disk(radius_px).astype(dtype)

    data = ndimage.convolve(data, kernel, mode='constant', cval=0)
    #TODO test that - it may be faster !
    #from scipy.signal import fftconvolve
    #data = fftconvolve(data, kernel, mode='same')

    profile.update(dtype=dtype)
    profile.pop("nodata", None)
    #profile.update(nodata=None)
    if compress is not None:
        profile.update(compress=compress)

    with rasterio.open(output_tiff, "w", **profile) as dst:
        dst.write(data, 1)



# compute circular kernel sum of band 1, but only for pixel values with same band 2 values
# use it for example, to compute neerby population in the same land mass / island
def circular_kernel_sum_per_code(
    input_tiff, # band 1: population. band 2: codes
    output_tiff,
    radius_m=120000,
    dtype=rasterio.float32,
    compress=None,
):
    with rasterio.open(input_tiff) as src:
        values = src.read(1)
        codes = src.read(2)
        profile = src.profile
        nodata = src.nodata
        pixel_size, pixel_size_y = src.res
        assert pixel_size == pixel_size_y, "Pixels must be square."

    if nodata is not None:
        values = np.where((values == nodata) | (values < 0), 0, values)
    else:
        values = np.clip(values, 0, None)

    values = values.astype(dtype)

    radius_px = int(radius_m / pixel_size)
    kernel = disk(radius_px).astype(dtype)

    output = np.zeros_like(values, dtype=dtype)
    unique_codes = np.unique(codes)

    for code in unique_codes:
        print("Processing", code)
        mask = (codes == code).astype(dtype)
        masked_values = values * mask
        summed = ndimage.convolve(masked_values, kernel, mode='constant', cval=0)
        output += np.where(codes == code, summed, 0)

    profile.update(dtype=dtype, count=1)
    profile.pop("nodata", None)
    if compress is not None:
        profile.update(compress=compress)

    with rasterio.open(output_tiff, "w", **profile) as dst:
        dst.write(output, 1)

'''
Same as previous but more efficient.
This avoids looping over codes one-by-one — much faster and cleaner.
Batch-processing all codes at once by:
 - Creating a 3D array masked_values_per_code where:
   - each slice masked_values_per_code[c] is values where codes == c, zero elsewhere
 - Convolve each slice separately
Then reconstruct the final raster by selecting, at each pixel, the result corresponding to its code
'''
def circular_kernel_sum_per_code_fast(
    input_tiff,
    output_tiff,
    radius_m=120000,
    dtype=rasterio.float32,
    compress=None,
):
    with rasterio.open(input_tiff) as src:
        values = src.read(1)
        codes = src.read(2)
        profile = src.profile
        nodata = src.nodata
        pixel_size, pixel_size_y = src.res
        assert pixel_size == pixel_size_y, "Pixels must be square."

    if nodata is not None:
        values = np.where((values == nodata) | (values < 0), 0, values)
    else:
        values = np.clip(values, 0, None)

    values = values.astype(dtype)
    codes = codes.astype(np.int32)

    radius_px = int(radius_m / pixel_size)
    kernel = disk(radius_px).astype(dtype)

    max_code = np.max(codes)
    h, w = values.shape

    # Pre-allocate masked value stacks (codes from 0 to max_code)
    masked_values = np.zeros((max_code + 1, h, w), dtype=dtype)

    # Fill masked values stack
    for c in range(max_code + 1):
        masked_values[c] = np.where(codes == c, values, 0)

    # Convolve each stack layer
    convolved = np.zeros_like(masked_values)
    for c in tqdm(range(max_code + 1), desc="Convolving code layers"):
        convolved[c] = ndimage.convolve(masked_values[c], kernel, mode='constant', cval=0)

    # Extract final output by selecting the convolved value at each pixel's code
    output = convolved[codes, np.indices((h, w))[0], np.indices((h, w))[1]]

    profile.update(dtype=dtype, count=1)
    profile.pop("nodata", None)
    if compress is not None:
        profile.update(compress=compress)

    with rasterio.open(output_tiff, "w", **profile) as dst:
        dst.write(output, 1)






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



def combine_geotiffs(input_files, output_file, output_bounds=None, compress=None, nodata_value = -9999):
    """
    Combine multiple GeoTIFF files into a single multi-band GeoTIFF.

    Parameters:
    - input_files: list of input GeoTIFF file paths.
    - output_file: path for the output GeoTIFF file.
    - output_bounds: optional tuple (minx, miny, maxx, maxy). If None, uses union of input bounds.
    """

    datasets = [rasterio.open(f) for f in input_files]

    # Check all have same CRS and resolution and nodata
    crs_set = set([ds.crs.to_string() for ds in datasets])
    res_set = set([(ds.res[0], ds.res[1]) for ds in datasets])

    if len(crs_set) > 1 or len(res_set) > 1:
        raise ValueError("All input GeoTIFFs must have the same CRS and resolution and nodata.")

    crs = datasets[0].crs
    res_x, res_y = datasets[0].res

    # Compute output bounds
    if output_bounds is None:
        minxs, minys, maxxs, maxys = zip(*[ds.bounds for ds in datasets])
        output_bounds = (
            min(minxs),
            min(minys),
            max(maxxs),
            max(maxys)
        )

    # Calculate output transform and shape
    width = int(np.ceil((output_bounds[2] - output_bounds[0]) / res_x))
    height = int(np.ceil((output_bounds[3] - output_bounds[1]) / abs(res_y)))
    transform = from_bounds(*output_bounds, width, height)

    # Prepare output metadata
    total_bands = sum(ds.count for ds in datasets)
    dtype = datasets[0].dtypes[0]  # Assuming all have same dtype

    out_meta = {
        'driver': 'GTiff',
        'height': height,
        'width': width,
        'count': total_bands,
        'crs': crs,
        'transform': transform,
        'dtype': dtype,
        'nodata': nodata_value,
    }

    # set compression
    if compress is not None:
        out_meta['compress'] = compress

    # Collect band names
    band_names = []
    for ds in datasets:
        for i in range(ds.count):
            name = ds.descriptions[i] if ds.descriptions[i] else f"{os.path.basename(ds.name)}_band{i+1}"
            band_names.append(name)

    # Write combined raster
    with rasterio.open(output_file, 'w', **out_meta) as dest:
        band_index = 1
        for ds in datasets:
            for i in range(ds.count):
                window = rasterio.windows.from_bounds(*output_bounds, transform=ds.transform)
                data = ds.read(
                    i+1,
                    out_shape=(height, width),
                    resampling=Resampling.nearest,
                    window=window,
                    masked=True
                )

                # Fill masked areas with nodata
                data_filled = np.where(data.mask, nodata_value, data.filled())

                dest.write(data_filled, band_index)
                dest.set_band_description(band_index, band_names[band_index-1])
                band_index += 1

                '''data = ds.read(i+1, out_shape=(height, width), resampling=rasterio.enums.Resampling.nearest, 
                               window=rasterio.windows.from_bounds(*output_bounds, transform=ds.transform))

                dest.write(data, band_index)
                dest.set_band_description(band_index, band_names[band_index-1])
                band_index += 1'''

    # Close input datasets
    for ds in datasets:
        ds.close()




# apply mask on a geotiff based on some geometries from a vector file
def geotiff_mask_by_countries(
          in_tiff_path,
          out_tiff_path,
          gpkg,
          gpkg_column,
          values_to_exclude,
          compress = None
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
    gdf = gdf[gdf[gpkg_column].isin(values_to_exclude)]

    # projection change, if needed
    if gdf.crs != crs:
        gdf = gdf.to_crs(crs)

    # make boolean mask (True = to mask)
    mask = geometry_mask(
        geometries=gdf.geometry,
        transform=transform,
        invert=True,  # True = pixels in the geometries are set to True
        out_shape=(height, width)
    )

    # get nodata value
    nodata_value = profile.get('nodata', None)
    if nodata_value is None:
        # Si pas de nodata défini, on en choisit un (exemple ici -9999)
        nodata_value = -9999
        profile.update(nodata=nodata_value)

    # apply mask to every band
    data[:, mask] = nodata_value

    # set compression
    if compress is not None:
        profile.update(compress=compress)

    # write output tiff
    with rasterio.open(out_tiff_path, 'w', **profile) as dst:
        dst.write(data)

