# compare V2 gpkg with clean production gpkg


# detect cells missing in V2 but present in production
import geopandas as gpd

prod = gpd.read_file("/home/juju/gisco/census_2021_production/census_grid_2021.gpkg")
v2 = gpd.read_file("/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg")

prod_cells = set(prod["GRD_ID"])
v2_cells = set(v2["GRD_ID"])
missing_in_v2 = prod_cells - v2_cells
missing_in_prod = v2_cells - prod_cells

print(f"Cells missing in V2 but present in production: {len(missing_in_v2)}")
print(f"Cells missing in production but present in V2: {len(missing_in_prod)}")


# save missing cells to gpkg
missing_in_v2_gdf = prod[prod["GRD_ID"].isin(missing_in_v2)]
missing_in_prod_gdf = v2[v2["GRD_ID"].isin(missing_in_prod)]
missing_in_v2_gdf.to_file("/home/juju/gisco/census_2021_validation/geodiff/missing_in_v2.gpkg", driver="GPKG")
missing_in_prod_gdf.to_file("/home/juju/gisco/census_2021_validation/geodiff/missing_in_prod.gpkg", driver="GPKG")

# loop through prod rows. for each row, get the row in v2 with the same GRD_ID
for idx, row in prod.iterrows():
    grd_id = row["GRD_ID"]
    v2_row = v2[v2["GRD_ID"] == grd_id]
    if v2_row.empty:
        print(f"GRD_ID {grd_id} missing in V2")
    else:
        # compare values in row and v2_row
        for col in prod.columns:
            prod_value = row[col]
            v2_value = v2_row.iloc[0][col]
            if prod_value != v2_value:
                print(f"GRD_ID {grd_id} column {col} differs: prod={prod_value} v2={v2_value}")

