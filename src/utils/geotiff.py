import rasterio
from rasterio.features import geometry_mask
import geopandas as gpd


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

