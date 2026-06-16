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
 




def join_csv_files(
    file_paths: list[str],
    id_column: str,
    output_path: str,
    join_type: str = "outer",
) -> None:
    """
    Join multiple CSV files on a shared ID column and write the result to a new CSV.
 
    Args:
        file_paths:  Ordered list of CSV file paths to join.
        id_column:   Name of the common ID column present in every file.
        output_path: Path where the merged CSV will be saved.
        join_type:   "inner" (only IDs present in ALL files) or
                     "outer" (all IDs, missing values filled with "").
    """
    if not file_paths:
        raise ValueError("file_paths must contain at least one file.")
    if join_type not in ("inner", "outer"):
        raise ValueError("join_type must be 'inner' or 'outer'.")
 
    def load(path: str) -> dict[str, dict]:
        """Return {id_value: {col: value, ...}} for one CSV file."""
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None or id_column not in reader.fieldnames:
                raise ValueError(
                    f"Column '{id_column}' not found in '{path}'. "
                    f"Available: {reader.fieldnames}"
                )
            return {row[id_column]: dict(row) for row in reader}
 
    tables = [load(p) for p in file_paths]
 
    # Determine the final set of IDs
    id_sets = [set(t.keys()) for t in tables]
    if join_type == "inner":
        all_ids = sorted(id_sets[0].intersection(*id_sets[1:]))
    else:  # outer
        all_ids = sorted(id_sets[0].union(*id_sets[1:]))
 
    # Collect all column names (ID column first, then the rest in file order)
    seen = {id_column}
    fieldnames = [id_column]
    for path, table in zip(file_paths, tables):
        sample = next(iter(table.values()), {})
        for col in sample:
            if col not in seen:
                fieldnames.append(col)
                seen.add(col)
 
    # Merge rows
    merged_rows = []
    for id_val in all_ids:
        row = {id_column: id_val}
        for table in tables:
            record = table.get(id_val, {})
            for col in fieldnames:
                if col == id_column:
                    continue
                if col in record:
                    row[col] = record[col]
                elif col not in row:
                    row[col] = ""   # fill missing with empty string
        merged_rows.append(row)
 
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_rows)

