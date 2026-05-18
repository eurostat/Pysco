"""
compare_geopackages.py
----------------------
Compare two GeoPackage files by a shared identifier (GRD_ID) and write
features with differing attribute values to an output GeoPackage.
 
Usage
-----
    python compare_geopackages.py \
        --ref   reference.gpkg \
        --cmp   to_compare.gpkg \
        --out   differences.gpkg \
        --attrs attr1 attr2 attr3 \
        [--ref-layer  LAYER_NAME] \
        [--cmp-layer  LAYER_NAME] \
        [--id-field   GRD_ID]

Output layer
------------
The output GeoPackage contains one feature per differing pair. Two extra
fields are added:
  • diff_fields   – comma-separated list of attributes that differ
  • diff_detail   – JSON string with {"attr": {"ref": ..., "cmp": ...}} entries

The geometry is taken from the *reference* file.
"""

import argparse
import json
import sys

import geopandas as gpd
import pandas as pd


# ---------------------------------------------------------------------------
# Core comparison logic
# ---------------------------------------------------------------------------

def load_layer(path: str, layer: str | None) -> gpd.GeoDataFrame:
    """Load a GeoPackage layer into a GeoDataFrame."""
    kwargs = {"filename": path}
    if layer: kwargs["layer"] = layer
    gdf = gpd.read_file(**kwargs)
    return gdf
 
 
def compare(
    ref: gpd.GeoDataFrame,
    cmp: gpd.GeoDataFrame,
    id_field: str,
    attrs: list[str],
) -> gpd.GeoDataFrame:
    """
    For every feature in *ref*, find the matching feature in *cmp* by
    *id_field* and compare the requested *attrs*.

    Returns a GeoDataFrame (same CRS as ref) containing only the features
    where at least one attribute differs, with two extra columns:
        diff_fields  str   comma-separated differing attribute names
        diff_detail  str   JSON {"attr": {"ref": val, "cmp": val}}
    """

    # --- basic validation ---------------------------------------------------
    missing_ref = [a for a in attrs if a not in ref.columns]
    missing_cmp = [a for a in attrs if a not in cmp.columns]
    if missing_ref:
        sys.exit(f"[ERROR] Attributes not found in reference layer: {missing_ref}")
    if missing_cmp:
        sys.exit(f"[ERROR] Attributes not found in comparison layer: {missing_cmp}")
    if id_field not in ref.columns:
        sys.exit(f"[ERROR] ID field '{id_field}' not found in reference layer.")
    if id_field not in cmp.columns:
        sys.exit(f"[ERROR] ID field '{id_field}' not found in comparison layer.")

    # --- index by id_field for fast lookup ----------------------------------
    cmp_indexed = cmp.set_index(id_field)

    diff_rows = []

    for _, ref_row in ref.iterrows():
        grd_id = ref_row[id_field]

        if grd_id not in cmp_indexed.index:
            # Feature exists only in ref – skip (or handle as desired)
            continue

        cmp_row = cmp_indexed.loc[grd_id]

        # If id_field is not unique, loc returns a DataFrame; take first row
        if isinstance(cmp_row, pd.DataFrame):
            cmp_row = cmp_row.iloc[0]

        # --- compare attributes ---------------------------------------------
        diffs = {}
        for attr in attrs:
            ref_val = ref_row[attr]
            cmp_val = cmp_row[attr]

            # Treat NaN == NaN as equal
            both_nan = pd.isna(ref_val) and pd.isna(cmp_val)
            if not both_nan and ref_val != cmp_val:
                diffs[attr] = {
                    "ref": None if pd.isna(ref_val) else ref_val,
                    "cmp": None if pd.isna(cmp_val) else cmp_val,
                }

        if diffs:
            row_data = ref_row.to_dict()
            row_data["diff_fields"] = ", ".join(diffs.keys())
            row_data["diff_detail"] = json.dumps(diffs, ensure_ascii=False, default=str)
            diff_rows.append(row_data)

    if not diff_rows:
        print("[INFO] No differences found.")
        return gpd.GeoDataFrame(columns=ref.columns.tolist() + ["diff_fields", "diff_detail"],
                                crs=ref.crs)

    result = gpd.GeoDataFrame(diff_rows, crs=ref.crs)
    return result



def main():
    parser = argparse.ArgumentParser(
        description="Compare two GeoPackage files and write differences to a new GeoPackage."
    )
    parser.add_argument("--ref",        required=True,  help="Path to the reference GeoPackage")
    parser.add_argument("--cmp",        required=True,  help="Path to the comparison GeoPackage")
    parser.add_argument("--out",        required=True,  help="Path for the output GeoPackage")
    parser.add_argument("--attrs",      required=True,  nargs="+",
                        help="Attribute names to compare (space-separated)")
    parser.add_argument("--ref-layer",  default=None,   help="Layer name in the reference file (optional)")
    parser.add_argument("--cmp-layer",  default=None,   help="Layer name in the comparison file (optional)")
    parser.add_argument("--id-field",   default="GRD_ID",
                        help="Identifier field name (default: GRD_ID)")
    parser.add_argument("--out-layer",  default="differences",
                        help="Output layer name (default: differences)")
    args = parser.parse_args()
 
    print(f"[INFO] Loading reference  : {args.ref}")
    ref = load_layer(args.ref, args.ref_layer)
    print(f"       → {len(ref)} features, columns: {list(ref.columns)}")
 
    print(f"[INFO] Loading comparison : {args.cmp}")
    cmp = load_layer(args.cmp, args.cmp_layer)
    print(f"       → {len(cmp)} features, columns: {list(cmp.columns)}")
 
    print(f"[INFO] Comparing attributes: {args.attrs}")
    result = compare(ref, cmp, args.id_field, args.attrs)
 
    print(f"[INFO] {len(result)} feature(s) with differences found.")
 
    if len(result) > 0:
        result.to_file(args.out, layer=args.out_layer, driver="GPKG")
        print(f"[INFO] Output written to   : {args.out}  (layer: '{args.out_layer}')")
    else:
        print("[INFO] Output file not written (nothing to save).")
 
 
if __name__ == "__main__":
    main()
 