import pandas as pd
import os




def decompose_hypercube(input_csv: str, output_folder: str, output_file_name_fun = None, verbose: bool = False) -> list[str]:
    """
    Decompose a hypercube CSV into one file per (UNIT, INDIC) combination.
 
    Each output file has the structure:
        GEO, VALUE_<time1>, VALUE_<time2>, ...
 
    Parameters
    ----------
    input_csv     : path to the input CSV file
    output_folder : directory where output CSV files will be written
                    (created if it does not exist)
 
    Returns
    -------
    List of paths to the files that were written.
    """
    os.makedirs(output_folder, exist_ok=True)
 
    df = pd.read_csv(input_csv)
 
    # Identify the dimension columns (everything except VALUE)
    dim_cols = [c for c in df.columns if c != "VALUE"]          # e.g. GEO TIME UNIT INDIC
    pivot_col = "TIME"                                           # becomes VALUE_XXXX columns
    group_cols = [c for c in dim_cols if c not in {"GEO", pivot_col}]  # e.g. UNIT INDIC
  
    for keys, group in df.groupby(group_cols):
        # Build a tidy label like "UNIT_NR__INDIC_T"
        if isinstance(keys, str):          # only one grouping column (edge-case)
            keys = (keys,)
        label_parts = [f"{col}_{val}" for col, val in zip(group_cols, keys)]
 
        # Pivot TIME → columns
        pivoted = (
            group
            .pivot_table(index="GEO", columns=pivot_col, values="VALUE", aggfunc="first")
            .reset_index()
        )
 
        # Rename columns: year integers → VALUE_YYYY
        pivoted.columns.name = None
        pivoted = pivoted.rename( columns=lambda c: f"{c}" if c != "GEO" else c)
 
        out_path = "_".join(label_parts)
        if output_file_name_fun: out_path = output_file_name_fun(out_path)
        out_path = os.path.join(output_folder, f"{out_path}.csv")
        pivoted.to_csv(out_path, index=False)
        if verbose: print(f"Written: {out_path}  ({len(pivoted)} rows, {list(pivoted.columns)})")
 



in_folder = "/home/juju/gisco/accessibility/stats/"
decompose_hypercube(in_folder + "euro_access_evrp_NUTS_2024.csv", in_folder + "decomposed/")

