import pandas as pd
import os



def decompose_hypercube(input_csv: str, output_folder: str, output_file_name_fun = None, verbose: bool = False,
                        id_columns:str = "GEO",
                        value_column:str = "VALUE",
                        time_column:str = "TIME",
) -> list[str]:
    """
    Decompose a hypercube CSV into one file per geo entity with one colmun per time values, and one file for other dimension combinations.
    (do pivot table)
 
    Each output file has the structure:
        id_columns, <time1>, <time2>, ...

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
 
    # Identify the dimension columns (everything except value_column)
    dim_cols = [c for c in df.columns if c != value_column]
    pivot_col = time_column
    group_cols = [c for c in dim_cols if c not in {id_columns, pivot_col}]
  
    for keys, group in df.groupby(group_cols):
        # Build a tidy label like "UNIT_NR__INDIC_T"
        if isinstance(keys, str):          # only one grouping column (edge-case)
            keys = (keys,)
        label_parts = [f"{col}_{val}" for col, val in zip(group_cols, keys)]
 
        # Pivot TIME → columns
        pivoted = (
            group
            .pivot_table(index=id_columns, columns=pivot_col, values=value_column, aggfunc="first")
            .reset_index()
        )
 
        # Rename columns
        pivoted.columns.name = None
        pivoted = pivoted.rename( columns=lambda c: f"{c}" if c != id_columns else c)
 
        out_path = "_".join(label_parts)
        if output_file_name_fun: out_path = output_file_name_fun(out_path)
        out_path = os.path.join(output_folder, f"{out_path}.csv")
        pivoted.to_csv(out_path, index=False)
        if verbose: print(f"Written: {out_path}  ({len(pivoted)} rows, {list(pivoted.columns)})")
 



in_folder = "/home/juju/gisco/accessibility/stats/"
service = "evrp"
geo = "NUTS_2024"
decompose_hypercube(in_folder + "euro_access_"+service+"_"+geo+".csv", in_folder + "decomposed/", output_file_name_fun = lambda f: "euro_access_"+service+"_"+geo+f)

