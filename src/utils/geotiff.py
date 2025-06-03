import rasterio
from rasterio.features import geometry_mask
import geopandas as gpd

from rasterio.merge import merge




def combine_geotiffs(input_files, output_file, output_bounds=None, compress=None):
    """
    Combine multiple GeoTIFF files into a single GeoTIFF.

    Parameters:
    - input_files: List of paths to input GeoTIFF files.
    - output_file: Path to the output GeoTIFF file.
    - output_bounds: Optional tuple specifying the output bounding box as (left, bottom, right, top).
    """

    # Open all input files
    src_files_to_mosaic = []
    for fp in input_files:
        src = rasterio.open(fp)
        src_files_to_mosaic.append(src)

    # Merge the files
    if output_bounds:
        mosaic, out_trans = merge(src_files_to_mosaic, bounds=output_bounds)
    else:
        mosaic, out_trans = merge(src_files_to_mosaic)

    # Copy the metadata from the first file
    out_meta = src_files_to_mosaic[0].meta.copy()

    # Update the metadata
    out_meta.update({
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_trans,
        "count": mosaic.shape[0],  # Number of bands
    })

    # set compression
    if compress is not None:
        out_meta.update(compress=compress)

    # Write the mosaic raster to disk
    with rasterio.open(output_file, "w", **out_meta) as dest:
        dest.write(mosaic)

    # Close all source files
    for src in src_files_to_mosaic:
        src.close()






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

