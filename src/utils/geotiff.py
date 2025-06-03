import rasterio
from rasterio.features import geometry_mask
import geopandas as gpd
from rasterio.merge import merge
from rasterio.coords import BoundingBox
from rasterio.transform import from_bounds
from rasterio.enums import Resampling
import numpy as np
import os




def combine_geotiffs(input_files, output_file, output_bounds=None, compress=None):
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
    nodata_values = set([ds.nodata for ds in datasets])

    if len(crs_set) > 1 or len(res_set) > 1 or len(nodata_values) > 1:
        raise ValueError("All input GeoTIFFs must have the same CRS and resolution and nodata.")

    crs = datasets[0].crs
    res_x, res_y = datasets[0].res
    nodata_value = datasets[0].nodata

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

