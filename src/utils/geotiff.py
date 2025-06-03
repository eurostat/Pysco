import rasterio
from rasterio.mask import mask
from rasterio.features import geometry_mask
import geopandas as gpd
#import numpy as np


def mask_raster_with_gpkg(input_raster_path, input_gpkg_path, attribute_name, attribute_values, output_raster_path):
    """
    Masque des pixels d'un GeoTIFF selon des polygones d'un GeoPackage filtrés par attribut.

    Args:
        input_raster_path (str): Chemin vers le GeoTIFF en entrée.
        input_gpkg_path (str): Chemin vers le GeoPackage contenant des polygones.
        attribute_name (str): Nom de l'attribut du GeoPackage à utiliser pour le filtre.
        attribute_values (list): Liste des valeurs à conserver pour filtrer les polygones.
        output_raster_path (str): Chemin vers le GeoTIFF de sortie.
    """
    # Lire le raster en entrée
    with rasterio.open(input_raster_path) as src:
        profile = src.profile.copy()
        data = src.read()
        transform = src.transform
        crs = src.crs
        height, width = src.height, src.width

    # Lire le GeoPackage et filtrer selon la liste des valeurs
    gdf = gpd.read_file(input_gpkg_path)
    gdf = gdf[gdf[attribute_name].isin(attribute_values)]

    # Reprojeter les polygones dans le CRS du raster si nécessaire
    if gdf.crs != crs:
        gdf = gdf.to_crs(crs)

    # Créer un masque booléen (True = à masquer)
    mask = geometry_mask(
        geometries=gdf.geometry,
        transform=transform,
        invert=True,  # True = pixels dans les géométries seront True
        out_shape=(height, width)
    )

    # Remplacer les pixels concernés par la valeur nodata sur toutes les bandes
    nodata_value = profile.get('nodata', None)
    if nodata_value is None:
        # Si pas de nodata défini, on en choisit un (exemple ici -9999)
        nodata_value = -9999
        profile.update(nodata=nodata_value)

    # Appliquer le masque sur chaque bande
    data[:, mask] = nodata_value

    # Écrire le raster de sortie
    with rasterio.open(output_raster_path, 'w', **profile) as dst:
        dst.write(data)

    print(f"Raster exporté : {output_raster_path}")



# apply mask on a geotiff based on some geometries from a vector file
def geotiff_mask_by_countries(
          in_tiff_path,
          out_tiff_path,
          values_to_exclude,
          gpkg = '/home/juju/geodata/gisco/CNTR_RG_100K_2024_3035.gpkg',
          gpkg_column = 'CNTR_ID',
          compress = None
):

        # load mask geometries
        gdf = gpd.read_file(gpkg)
        gdf = gdf[ gdf[gpkg_column].isin(values_to_exclude) ]

        # apply mask
        with rasterio.open(in_tiff_path) as src:
            out_image, out_transform = mask(src, gdf.geometry, crop=True, nodata=src.nodata, invert=True)
            out_meta = src.meta.copy()

        # update metadata
        out_meta.update({"driver": "GTiff",
                        "height": out_image.shape[1],
                        "width": out_image.shape[2],
                        "transform": out_transform,
                        "compress": "none" if compress is None else compress
                        })

        # save output
        with rasterio.open(out_tiff_path, "w", **out_meta) as dest:
            dest.write(out_image)

