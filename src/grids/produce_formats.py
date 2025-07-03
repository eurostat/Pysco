
import geopandas as gpd
import os

folder = "/home/juju/geodata/gisco/grids/"

for res in ["100", "50", "20", "10", "5", "2", "1"]:

    grid = folder + "grid_"+res+"km_surf.gpkg"

    print("load gpkg grid", res+"000m")
    gdf = gpd.read_file(grid)

    print("save gpkg point", res+"000m")
    gdf['geometry'] = gdf.geometry.centroid
    f = folder + "grid_"+res+"km_point.gpkg"
    if os.path.exists(f): os.remove(f)
    gdf.to_file(f, driver="GPKG")

    print("save CSV", res+"000m")
    gdf = gdf.drop(columns='geometry')
    gdf.to_csv(folder + "grid_"+res+"km.csv", index=False)

    print("save parquet", res+"000m")
    gdf.to_parquet(folder + "grid_"+res+"km.parquet", index=False)

