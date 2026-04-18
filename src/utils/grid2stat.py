# functions to aggregate statistics from grid to statistical units.

import rasterio
import geopandas as gpd
import pandas as pd
from rasterio.features import geometry_mask



def grid2stat(grid_tiff, stat_gpkg, stat_id, out_csv):
    """
    Aggregate statistics from grid to statistical units.

    Parameters
    ----------
    grid_tiff : str
        Path to the input grid TIFF file.
    stat_gpkg : str
        Path to the input statistical units GeoPackage file.
    stat_id : str
        Name of the identifier column in the statistical units GeoPackage.
    out_csv : str
        Path to the output CSV file where aggregated statistics will be saved.

    Returns
    -------
    None
        The function saves the aggregated statistics to a CSV file.
    """

    # Read the grid TIFF file
    with rasterio.open(grid_tiff) as src:
        grid_data = src.read(1)
        grid_transform = src.transform

    # Read the statistical units GeoPackage file
    stat_units = gpd.read_file(stat_gpkg)

    # Initialize a list to store results
    results = []

    # Loop through each statistical unit and aggregate statistics from the grid
    for index, row in stat_units.iterrows():
        stat_id_value = row[stat_id]
        geometry = row['geometry']

        # Create a mask for the current statistical unit
        mask = geometry_mask([geometry], transform=grid_transform, invert=True, out_shape=grid_data.shape)

        # Extract values from the grid that fall within the mask
        masked_values = grid_data[mask]

        # Calculate statistics (e.g., mean, sum) for the masked values
        mean_value = masked_values.mean()
        sum_value = masked_values.sum()

        # Append results to the list
        results.append({
            stat_id: stat_id_value,
            'mean': mean_value,
            'sum': sum_value
        })

    # Convert results to a DataFrame and save to CSV
    results_df = pd.DataFrame(results)
    results_df.to_csv(out_csv, index=False)


