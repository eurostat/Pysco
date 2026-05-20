# compare V2 with v3 gpkg


import geopandas as gpd
import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.compare_gpkg import compare



print(datetime.now(), "Loading v3 GPKG...")
v3 = gpd.read_file("/home/juju/gisco/census_2021_v3_production/ESTAT_Census_2021_V3.gpkg")
print(datetime.now(), f"V3: {len(v3)} features")

print(datetime.now(), "Loading v2 GPKG...")
v2 = gpd.read_file("/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg")
print(datetime.now(), f"V2: {len(v2)} features")


if True:
    data = {
        "T": ["T"],
        "SEX": ["M", "F"],
        "AGE": ["Y_LT15", "Y_1564", "Y_GE65"],
        "EMP": ["EMP"],
        "BIRT": ['NAT', 'EU_OTH', 'OTH'],
        "MOVE": ['SAME', 'CHG_IN', 'CHG_OUT'],
        "LAND_SURFACE": ['LAND_SURFACE'],
        "POPULATED": ['POPULATED']
    }

    for group, attrs in data.items():
        print(datetime.now(), f"Comparing group {group} with attributes {attrs}")
        out = compare(
            ref=v3,
            cmp=v2,
            id_field="GRD_ID",
            attrs=attrs
            )
        print(datetime.now(), f"Group {group} comparison done. Nb differences: {len(out)}")
        out.to_file("/home/juju/gisco/census_2021_v2_validation/geodiff/diffs_"+group+".gpkg", driver="GPKG")




# get the missing cells
if True:

    v3_cells = set(v3["GRD_ID"])
    v2_cells = set(v2["GRD_ID"])
    missing_in_v2 = v3_cells - v2_cells
    missing_in_v3 = v2_cells - v3_cells

    print(datetime.now(), f"Cells missing in V2 but present in V3: {len(missing_in_v2)}")
    print(datetime.now(), f"Cells missing in V3 but present in V2: {len(missing_in_v3)}")


    # save missing cells to gpkg
    missing_in_v2_gdf = v3[v3["GRD_ID"].isin(missing_in_v2)]
    missing_in_v3_gdf = v2[v2["GRD_ID"].isin(missing_in_v3)]
    missing_in_v2_gdf.to_file("/home/juju/gisco/census_2021_v2_validation/geodiff/missing_in_v2.gpkg", driver="GPKG")
    missing_in_v3_gdf.to_file("/home/juju/gisco/census_2021_v2_validation/geodiff/missing_in_v3.gpkg", driver="GPKG")

