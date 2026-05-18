# compare V2 gpkg with clean production gpkg


# detect cells missing in V2 but present in production
import geopandas as gpd
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.compare_gpkg import compare



prod_path = "/home/juju/gisco/census_2021_production/census_grid_2021.gpkg"
v2_path = "/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg"

compare(
    ref=gpd.read_file(prod_path),
    cmp=gpd.read_file(v2_path),
    id_field="GRD_ID",
    attrs=['T', 'M', 'F', 'Y_LT15', 'Y_1564', 'Y_GE65', 'EMP', 'NAT', 'EU_OTH', 'OTH', 'SAME', 'CHG_IN', 'CHG_OUT', 'LAND_SURFACE', 'POPULATED',]
    )




# get the missing cells
if False:
    prod = gpd.read_file(prod_path)
    v2 = gpd.read_file(v2_path)

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

