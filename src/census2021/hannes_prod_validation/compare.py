# compare V2 gpkg with clean production gpkg


# detect cells missing in V2 but present in production
import geopandas as gpd
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.compare_gpkg import compare


prod = gpd.read_file("/home/juju/gisco/census_2021_production/census_grid_2021.gpkg")
print(f"Production: {len(prod)} features")
v2 = gpd.read_file("/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg")
print(f"V2: {len(v2)} features")



data = {
    "T": ["T"],
    "SEX": ["M", "F"],
    "AGE": ["Y_LT15", "Y_1564", "Y_GE65"],
    "EMP": ["EMP"],
    "BIRT": ['NAT', 'EU_OTH', 'OTH'],
    "MOVE": ['SAME', 'CHG_IN', 'CHG_OUT'],
    "LAND": ['LAND_SURFACE'],
    "POP": ['POPULATED']
}

for group, attrs in data.items():
    print(f"Comparing group {group} with attributes {attrs}")
    compare(
        ref=prod,
        cmp=v2,
        id_field="GRD_ID",
        attrs=attrs
        ).to_file("/home/juju/gisco/census_2021_validation/geodiff/diffs"+group+".gpkg", driver="GPKG")




# get the missing cells
if False:

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

