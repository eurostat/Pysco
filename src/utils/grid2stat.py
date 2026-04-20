# functions to aggregate statistics from grid to statistical units.

import rasterio
import fiona
from shapely.geometry import shape
from rasterio.features import geometry_mask
import pandas as pd
import numpy as np

#TODO
# get mask values with indices
# test with aggregation based on several bands, from separate tiffs ?
# use generic iterator instead of gpkg file
# check what happens when centre exactly on the limit - counted twice ?
# handle intersection-area weighted case - with exact intersection computation or 10*resampling ?
# export as parquet

def grid2stat(grid_tiff, stat_gpkg, stat_id, out_csv, band=1, out_dict=None):
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
    out_dict : dict, optional
        A dictionnary describing the output data. One entry per aggregated indicator. The key is the column name. The value is the aggregation function to use to compute the aggregated value from the cell values.
        Default is None, in which case it will be the sum of the cell values.
    Returns
    -------
    None
        The function saves the aggregated statistics to a CSV file.
    """

    # Open the grid TIFF file
    with rasterio.open(grid_tiff) as grid:
        grid_data = grid.read(band)
        grid_transform = grid.transform

    # Prepare default aggregation function
    aggegation_func_default = lambda arr: arr.sum()  # Default to sum if no custom function is provided

    # Default to a single column with default aggregation function if no custom dict is provided
    if out_dict is None: out_dict = { "sum": aggegation_func_default }

    # Initialize a list to store results
    results = []

    # Loop through each statistical unit and aggregate statistics from the grid
    with fiona.open(stat_gpkg) as fs:
        for f in fs:
            sid = f["properties"][stat_id]
            print(sid)

            # Make geometry from the feature
            g = shape(f["geometry"])

            # Create a mask for the current statistical unit - True for pixels whose centres fall within the geometry, False otherwise
            mask = geometry_mask([g], transform=grid_transform, invert=True, out_shape=grid_data.shape, all_touched=False)

            # Extract values from the grid that fall within the mask
            masked_values = grid_data[mask]
            #print(masked_values)

            #masked = np.where(mask, grid_data, np.nan)
            #print(masked)

            rows, cols = np.where(mask)
            values = grid_data[rows, cols]
            #print(len(rows))
            #print(len(cols))
            #print(len(values))

            # filter to remove no_data values
            if grid.nodata is not None:
                masked_values = masked_values[masked_values != grid.nodata]  

            #print(type(masked_values))
            #print(masked_values)

            # Make output result
            result = { stat_id: str(sid) }

            # Calculate aggregates value
            for out_col, aggegation_func in out_dict.items():
                if aggegation_func is None: aggegation_func = aggegation_func_default
                agg_value = aggegation_func(masked_values)
                result[out_col] = agg_value
            #print(result)

            # Append results to the list
            results.append(result)

    # Save to CSV
    pd.DataFrame(results).to_csv(out_csv, index=False)



# test
grid2stat("/home/juju/geodata/census/2018/JRC_1K_POP_2018_clean.tif",
          "/home/juju/Bureau/test.gpkg",
          #"/home/juju/geodata/gisco/NUTS_RG_100K_2024_3035.gpkg",
          "NUTS_ID",
          "/home/juju/Bureau/out.csv",
          band=1,
          out_dict={
            "sum": lambda arr: arr.sum(),
            "mean": lambda arr: arr.mean(),
            "max": lambda arr: arr.max(),
            "min": lambda arr: arr.min(),
            "count": lambda arr: len(arr)
          }
          )

