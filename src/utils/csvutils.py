import os
import sys
import tempfile
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

















def hypercube_to_timeseries_large(
    source,                               # path to CSV, or an already-loaded DataFrame
    output_folder: str,
    id_column: str = "GEO",
    value_column: str = "VALUE",
    time_column: str = "TIME",
    output_file_name_fun=None,
    chunksize: int = 1_000_000,
    verbose: bool = False,
):
    """
    Decompose a hypercube into one pivoted CSV per combination of the other
    dimensions (rows = id_column, columns = time values).

    Memory-friendly: pass 1 streams the input in chunks and appends each row to
    a temporary partition file (one per dimension combination); pass 2 pivots
    one partition at a time. Peak memory ~ one chunk, or the largest single
    partition, whichever is bigger.

    Parameters
    ----------
    source : str | os.PathLike | pd.DataFrame
        CSV path (recommended for large data) or a DataFrame.
    output_file_name_fun : callable, optional
        Maps the label string (e.g. "UNIT_NR__INDIC_T") to a file name
        without the ".csv" extension.
    chunksize : int
        Rows per chunk when reading the CSV.
    """
    os.makedirs(output_folder, exist_ok=True)

    # ---- chunk iterator (everything read as str: no dtype guessing, exact output)
    if isinstance(source, pd.DataFrame):
        def chunks():
            for start in range(0, len(source), chunksize):
                yield source.iloc[start:start + chunksize]
        header_cols = list(source.columns)
    else:
        header_cols = list(pd.read_csv(source, nrows=0).columns)

        def chunks():
            yield from pd.read_csv(source, dtype=str, chunksize=chunksize)

    group_cols = [c for c in header_cols
                  if c not in {value_column, id_column, time_column}]
    keep_cols = [id_column, time_column, value_column]

    with tempfile.TemporaryDirectory() as tmp:
        partitions = {}   # key tuple -> temp file path

        # ---------- Pass 1: partition rows by dimension combination ----------
        for chunk in chunks():
            chunk = chunk.astype({c: str for c in group_cols})
            if group_cols:
                grouped = chunk.groupby(group_cols, sort=False, observed=True)
            else:
                grouped = [((), chunk)]

            for keys, g in grouped:
                if not isinstance(keys, tuple):
                    keys = (keys,)
                path = partitions.get(keys)
                new = path is None
                if new:
                    path = os.path.join(tmp, f"part_{len(partitions)}.csv")
                    partitions[keys] = path
                # append mode keeps original row order -> "first" semantics preserved
                g[keep_cols].to_csv(path, mode="a", header=False, index=False)
            del chunk

        # ---------- Pass 2: pivot one partition at a time ----------
        for keys, path in partitions.items():
            part = pd.read_csv(path, names=keep_cols, dtype=str)

            # equivalent of aggfunc="first", but far cheaper than pivot_table
            part = part.drop_duplicates(subset=[id_column, time_column], keep="first")

            pivoted = part.pivot(index=id_column, columns=time_column, values=value_column)
            pivoted = pivoted.reindex(sorted(pivoted.columns), axis=1).reset_index()
            pivoted.columns.name = None
            pivoted.columns = [str(c) for c in pivoted.columns]

            label = "__".join(f"{col}_{val}" for col, val in zip(group_cols, keys))
            name = output_file_name_fun(label) if output_file_name_fun else label
            out_path = os.path.join(output_folder, f"{name}.csv")
            pivoted.to_csv(out_path, index=False)

            if verbose:
                print(f"Written: {out_path}  ({len(pivoted)} rows, {pivoted.shape[1]} columns)")

            os.remove(path)
            del part, pivoted




def hypercube_to_timeseries(
        df,
        output_folder: str,
        id_column:str = "GEO",
        value_column:str = "VALUE",
        time_column:str = "TIME",
        output_file_name_fun = None,
        verbose: bool = False,
):
    """
    Decompose a hypercube CSV into one file per geo entity with one colmun per time values, and one file for other dimension combinations.
    (do pivot table)
 
    Each output file has the structure:
        id_column, <time1>, <time2>, ...

    Parameters
    ----------
    df     : input dataframe
    output_file_name_fun : A function that returns an output file name from a string with dimension info. Without ".csv" extension.

    """
  
    os.makedirs(output_folder, exist_ok=True)
 
    # Identify the dimension columns (everything except value_column)
    dim_cols = [c for c in df.columns if c != value_column]
    pivot_col = time_column
    group_cols = [c for c in dim_cols if c not in {id_column, pivot_col}]
  
    for keys, group in df.groupby(group_cols):
        # Build a tidy label like "UNIT_NR__INDIC_T"
        if isinstance(keys, str):          # only one grouping column (edge-case)
            keys = (keys,)
        label_parts = [f"{col}_{val}" for col, val in zip(group_cols, keys)]
 
        # Pivot TIME → columns
        pivoted = (
            group
            .pivot_table(index=id_column, columns=pivot_col, values=value_column, aggfunc="first")
            .reset_index()
        )
 
        # Rename columns
        pivoted.columns.name = None
        pivoted = pivoted.rename( columns=lambda c: f"{c}" if c != id_column else c)
 
        out_path = "__".join(label_parts)
        if output_file_name_fun: out_path = output_file_name_fun(out_path)
        out_path = os.path.join(output_folder, f"{out_path}.csv")
        pivoted.to_csv(out_path, index=False)
        if verbose: print(f"Written: {out_path}  ({len(pivoted)} rows, {list(pivoted.columns)})")
 
