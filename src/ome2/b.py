from geopandas.tools import overlay


intersection = overlay(gdf1, gdf2, how='intersection')

