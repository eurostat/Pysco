import sys
from pathlib import Path
import fiona
import geopandas as gpd
from shapely.geometry import MultiPoint


def check_multipoint_components(path: str | Path) -> None:
    with fiona.open(path) as src:
        if src.schema["geometry"] not in ("MultiPoint", "Unknown"):
            print(f"Warning: layer geometry type is '{src.schema['geometry']}', expected MultiPoint")

        singles = []
        multiples = []
        invalid = []

        for feature in src:
            fid = feature["id"]
            geom = feature["geometry"]

            if geom is None:
                invalid.append(fid)
                continue

            if geom["type"] != "MultiPoint":
                invalid.append(fid)
                continue

            n = len(geom["coordinates"])
            if n == 1: singles.append(fid)
            else: multiples.append(fid)

        # Summary
        total = len(singles) + len(multiples) + len(invalid)
        print(f"\nFile   : {path}")
        print(f"Total  : {total} features")
        print(f"Single : {len(singles)}")
        print(f"Multi  : {len(multiples)}")
        print(f"Invalid: {len(invalid)}")




def multipoint_to_point(src_path: str | Path, dst_path: str | Path) -> None:
    src_path = Path(src_path)
    dst_path = Path(dst_path)

    gdf = gpd.read_file(src_path)

    invalid_mask = gdf.geometry.isna() | ~gdf.geometry.type.isin(["MultiPoint"])
    if invalid_mask.any():
        print(f"Skipping {invalid_mask.sum()} null or non-MultiPoint features")
        gdf = gdf[~invalid_mask]

    # Explode MultiPoint -> Point (vectorised, no Python loop over features)
    gdf_points = gdf.explode(index_parts=False).reset_index(drop=True)

    gdf_points.to_file(dst_path, driver="GPKG")

    print(f"Input  : {src_path}  ({len(gdf)} features)")
    print(f"Output : {dst_path}  ({len(gdf_points)} points written)")




#check_multipoint_components("/home/juju/geodata/gisco/recharging_points/evrp_2024_3035.gpkg")
multipoint_to_point("/home/juju/geodata/gisco/recharging_points/evrp_2024_3035___.gpkg", "/home/juju/geodata/gisco/recharging_points/evrp_2024_3035.gpkg")

