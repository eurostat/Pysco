import os
import sys
 
import pandas as pd
import csv

def save_as_csv(csv_filename, dictionaries_array):
    with open(csv_filename, mode="w", newline="") as file:
        fieldnames = dictionaries_array[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dictionaries_array)



def transform_csv_columns(
    input_path: str,
    transform_fn,
    exclude_column: str,
    output_path: str = None,
) -> None:
    """
    Read a CSV file, apply a function to each column name except one, and save the result.
 
    Args:
        input_path:     Path to the input CSV file.
        transform_fn:   A callable applied to every column name except the excluded one.
        exclude_column: The column name that should remain unchanged. Typically, the ID columns
        output_path:    Path where the transformed CSV will be saved.
    """

    if output_path is None:
        output_path = input_path

    with open(input_path, newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        original_columns = list(reader.fieldnames)
 
        if exclude_column not in original_columns:
            raise ValueError(
                f"Column '{exclude_column}' not found. "
                f"Available columns: {original_columns}"
            )
 
        # Build a mapping from old name → new name
        rename_map = {
            col: (col if col == exclude_column else transform_fn(col))
            for col in original_columns
        }
        new_columns = [rename_map[col] for col in original_columns]

        rows = [
            {rename_map[k]: v for k, v in row.items()}
            for row in reader
        ]

    with open(output_path, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=new_columns)
        writer.writeheader()
        writer.writerows(rows)
 



def join_csvs(
    files: list[str],
    output: str,
    add_source_column: bool = False,
    ignore_index: bool = True,
    verboce: bool = False,
) -> None:
    if not files:
        print("No CSV files found. Nothing to do.", file=sys.stderr)
        sys.exit(1)
 
    frames = []
    for path in files:
        try:
            df = pd.read_csv(path)
            if add_source_column:
                df.insert(0, "_source_file", os.path.basename(path))
            frames.append(df)
            if verboce: print(f"  ✓ {path}  ({len(df):,} rows, {len(df.columns)} cols)")
        except Exception as exc:
            if verboce: print(f"  ✗ {path}  ERROR: {exc}", file=sys.stderr)
 
    if not frames:
        if verboce: print("All files failed to load.", file=sys.stderr)
        sys.exit(1)
 
    merged = pd.concat(frames, ignore_index=ignore_index)
    merged.to_csv(output, index=False)
    if verboce: print(f"\nDone — {len(merged):,} total rows written to '{output}'")
 

 