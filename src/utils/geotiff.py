import rasterio
from rasterio.mask import mask
import geopandas as gpd


# apply mask on a geotiff based on some geometries from a vector file
def geotiff_mask_by_countries(
          in_tiff_path,
          out_tiff_path,
          values_to_exclude,
          gpkg = '/home/juju/geodata/gisco/admin_tagging/final.gpkg',
          gpkg_column = 'CNTR_ID',
):

        # load mask geometries
        gdf = gpd.read_file(gpkg)
        gdf = gdf[~gdf[gpkg_column].isin(values_to_exclude)]

        # apply mask
        with rasterio.open(in_tiff_path) as src:
            out_image, out_transform = mask(src, gdf.geometry, crop=True, nodata=src.nodata)
            out_meta = src.meta.copy()

        # update metadata
        out_meta.update({"driver": "GTiff",
                        "height": out_image.shape[1],
                        "width": out_image.shape[2],
                        "transform": out_transform})

        # save output
        with rasterio.open(out_tiff_path, "w", **out_meta) as dest:
            dest.write(out_image)

