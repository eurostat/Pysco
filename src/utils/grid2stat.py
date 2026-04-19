# functions to aggregate statistics from grid to statistical units.

import rasterio
import geopandas as gpd
import pandas as pd
from rasterio.features import geometry_mask


#TODO
# test with custom aggregation function
# test with aggregation based on several bands, from separate tiffs ?
# read gpkg with fiona
# use generic iterator instead of gpkg file
# check no_data values handling
# check how pixel centres are handled in the geometry mask - what happens when a pixel is partially covered by the geometry ? when centre exactly on the limit - counted twice ?


def grid2stat(grid_tiff, stat_gpkg, stat_id, out_csv, band=1, out_col=None, aggegation_func=None):
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
    band : int, optional
        Band number to read from the grid TIFF file (default is 1).
    out_col : str, optional
        Name of the output column in the CSV file for the aggregated statistic (default is None, which will use the name of the input band).
    aggegation_func : function, optional
        Custom aggregation function to apply to the masked values (default is None, which will use sum).

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

    # Set the aggregation function
    if aggegation_func is None:
        aggegation_func = lambda arr: arr.sum()  # Default to sum if no custom function is provided

    # Initialize a list to store results
    results = []

    # Loop through each statistical unit and aggregate statistics from the grid
    for index, row in stat_units.iterrows():
        print(row[stat_id])
        geom = row['geometry']

        # Create a mask for the current statistical unit - True for pixels whose centres fall within the geometry, False otherwise
        mask = geometry_mask([geom], transform=grid_transform, invert=True, out_shape=grid_data.shape, all_touched=False)

        # Extract values from the grid that fall within the mask
        masked_values = grid_data[mask]

        # filter to remove no_data values
        masked_values = masked_values[masked_values != src.nodata]  

        #print(type(masked_values))
        #print(masked_values)

        # Calculate aggregates value
        agg_value = aggegation_func(masked_values)

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
          "/home/juju/Bureau/test.gpkg",
          #"/home/juju/geodata/gisco/NUTS_RG_100K_2024_3035.gpkg",
          "NUTS_ID",
          "/home/juju/Bureau/out.csv",
          band=1, out_col="popu_2018", aggegation_func=lambda arr: arr.max()
          )

