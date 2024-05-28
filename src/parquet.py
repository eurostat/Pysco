import pandas as pd


def convert_parquet_compression(input_file_path, output_file_path, output_compression='snappy'):
    """
    Convert a Parquet file from one compression format to another.

    Parameters:
    - input_file_path: str, path to the input Parquet file.
    - output_file_path: str, path to the output Parquet file.
    - output_compression: str, compression type for the output Parquet file (default 'snappy').
    """
    # Read the Parquet file into a DataFrame
    df = pd.read_parquet(input_file_path, engine='pyarrow')

    # Write the DataFrame to a new Parquet file with the desired compression
    df.to_parquet(output_file_path, engine='pyarrow', compression=output_compression)


convert_parquet_compression("/home/juju/workspace/gridviz/assets/parquet/Europe/pop_2018_5km.parquet", "/home/juju/workspace/gridviz/assets/parquet/Europe/pop_2018_5km_snappy.parquet")
