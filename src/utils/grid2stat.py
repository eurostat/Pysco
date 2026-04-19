# functions to aggregate statistics from grid to statistical units.

import rasterio
import geopandas as gpd
import pandas as pd
from rasterio.features import geometry_mask


#TODO
# test simple example
# test with custom aggregation function
# test with aggregation based on several bands, from separate tiffs ?
# read gpkg with fiona
# use generic iterator instead of gpkg file
# check no_data values handling
# check how pixel centres are handled in the geometry mask - what happens when a pixel is partially covered by the geometry ? when centre exactly on the limit - counted twice ?


def grid2stat(grid_tiff, stat_gpkg, stat_id, out_csv, band=1, out_col=None):
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

    # Open the grid TIFF file
    with rasterio.open(grid_tiff) as src:
        grid_data = src.read(band)
        grid_transform = src.transform

    # Read the statistical units GeoPackage file
    stat_units = gpd.read_file(stat_gpkg)

    # Initialize a list to store results
    results = []

    # Loop through each statistical unit and aggregate statistics from the grid
    for index, row in stat_units.iterrows():

        # Create a mask for the current statistical unit
        mask = geometry_mask([row['geometry']], transform=grid_transform, invert=True, out_shape=grid_data.shape)

        # Extract values from the grid that fall within the mask
        masked_values = grid_data[mask]

        # Calculate aggregates value
        agg_value = masked_values.sum()

        # Make output result
        result = { stat_id: str(row[stat_id]) }
        result[out_col] = agg_value

        # Append results to the list
        results.append(result)

    # Convert results to a DataFrame and save to CSV
    results_df = pd.DataFrame(results)
    results_df.to_csv(out_csv, index=False)



# test
grid2stat("/home/juju/geodata/census/2018/JRC_1K_POP_2018_clean.tif",
          "/home/juju/geodata/gisco/NUTS_RG_100K_2024_3035.gpkg",
          "NUTS_ID",
          "/home/juju/Bureau/out.csv",
          band=1, out_col="popu_2018")

