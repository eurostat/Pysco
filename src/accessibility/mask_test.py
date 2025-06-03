import rasterio
from rasterio.mask import mask
import geopandas as gpd


# Charger le fichier vectoriel GPKG
gdf = gpd.read_file('votre_fichier.gpkg')

# Supposons que vous ayez une colonne 'nom' et que vous vouliez filtrer par une valeur spécifique
gdf_filtered = gdf[gdf['nom'] == 'valeur_d_interet']

# Ensuite, utilisez gdf_filtered au lieu de gdf dans la fonction mask
with rasterio.open('votre_fichier.tif') as src:
    out_image, out_transform = mask(src, gdf_filtered.geometry, crop=True, nodata=src.nodata)
    out_meta = src.meta.copy()

# Mettre à jour les métadonnées
out_meta.update({"driver": "GTiff",
                 "height": out_image.shape[1],
                 "width": out_image.shape[2],
                 "transform": out_transform})

# Sauvegarder le résultat
with rasterio.open('fichier_masque.tif', "w", **out_meta) as dest:
    dest.write(out_image)


