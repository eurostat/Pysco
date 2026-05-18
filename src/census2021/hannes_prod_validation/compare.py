# compare V2 gpkg with clean production gpkg


# detect cells missing in V2 but present in production
import geopandas as gpd

prod = gpd.read_file("/home/juju/gisco/census_2021_production/census_grid_2021.gpkg")
v2 = gpd.read_file("/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg")

prod_cells = set(prod["cell_id"])
v2_cells = set(v2["cell_id"])
missing_in_v2 = prod_cells - v2_cells
missing_in_prod = v2_cells - prod_cells

print(f"Cells missing in V2 but present in production: {len(missing_in_v2)}")
print(f"Cells missing in production but present in V2: {len(missing_in_prod)}")


# save missing cells to gpkg
missing_in_v2_gdf = prod[prod["cell_id"].isin(missing_in_v2)]
missing_in_prod_gdf = v2[v2["cell_id"].isin(missing_in_prod)]
missing_in_v2_gdf.to_file("/home/juju/gisco/census_2021_validation/geodiff/missing_in_v2.gpkg", driver="GPKG")
missing_in_prod_gdf.to_file("/home/juju/gisco/census_2021_validation/geodiff/missing_in_prod.gpkg", driver="GPKG")

