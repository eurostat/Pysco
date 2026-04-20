# functions to aggregate statistics from grid to statistical units.

import rasterio
import fiona
from shapely.geometry import shape
from rasterio.features import geometry_mask
import pandas as pd
import numpy as np
from datetime import datetime

#TODO
# get mask values with indices
# test with aggregation based on several bands, from separate tiffs ?

# array of input geopackages ?
# use generic iterator instead of gpkg file
# check what happens when centre exactly on the limit - counted twice ?
# handle intersection-area weighted case - with exact intersection computation or 10*resampling ?
# export as parquet

def grid2stat(tiffs, stat_gpkg, stat_id, out_csv, out_dict=None, verbose=False):
    """
    Aggregate statistics from grid to statistical units.

    Parameters
    ----------
    tiffs : arr
        An array with the input grid TIFF files. One element per input tiff. Each element is a pair of the tiff file path and the tiff band number.
        NB: all tiff files must have the same resolution, geotransform and extent. TODO check
    stat_gpkg : str
        Path to the input statistical units GeoPackage file.
    stat_id : str
        Name of the identifier column in the statistical units GeoPackage.
    out_csv : str
        Path to the output CSV file where aggregated statistics will be saved.
    out_dict : dict, optional
        A dictionnary describing the output data. One entry per aggregated indicator. The key is the column name. The value is the aggregation function to use to compute the aggregated value from the cell values.
        Default is None, in which case it will be the sum of the cell values.
    Returns
    -------
    None
        The function saves the aggregated statistics to a CSV file.
    """

    # Open the grid TIFF files
    grid_data = []
    grid_transform = []
    grid_nodata = []
    for grid_tiff, band in tiffs:
        with rasterio.open(grid_tiff) as grid:
            grid_data.append(grid.read(band))
            grid_transform.append(grid.transform)
            grid_nodata.append(grid.nodata)

    # Prepare default aggregation function
    aggegation_func_default = lambda arr: np.sum([x for x in arr if x is not None])  # Default to sum if no custom function is provided

    # If not specified, set default to a single column with default aggregation function if no custom dict is provided
    if out_dict is None: out_dict = { "sum": aggegation_func_default }

    # Initialize a list to store results
    results = []

    # Loop through each statistical unit and aggregate statistics from the grid
    with fiona.open(stat_gpkg) as fs:
        for f in fs:
            sid = f["properties"][stat_id]
            if verbose: print(datetime.now(), sid)

            # Make geometry from the feature, for masking the grids
            g = shape(f["geometry"])

            values = []
            for i in range(len(grid_data)):
                # Create mask - True for pixels whose centres fall within the geometry, False otherwise
                mask = geometry_mask([g], transform=grid_transform[i], invert=True, out_shape=grid_data[i].shape, all_touched=False)

                # get masked values, with indices
                rows, cols = np.where(mask)
                v = grid_data[i][rows, cols]
                #print(rows, cols)

                # filter to remove no_data values
                nd = grid_nodata[i]
                if nd is not None:
                    v = np.array(v, dtype=object)
                    v[v == nd] = None
                    #v = v[v != nd]  

                values.append(v)

            # Structure values as array of arrays, one per band. One element is a list of band values for a pixel.
            #TODO

            # Make output result
            result = { stat_id: str(sid) }

            # Calculate aggregates value
            for out_col, aggegation_func in out_dict.items():
                if aggegation_func is None: aggegation_func = aggegation_func_default
                #agg_value = aggegation_func(masked_values)
                agg_value = aggegation_func(values[0]) #TODO - handle several bands
                result[out_col] = agg_value
            #print(result)

            # Append results to the list
            results.append(result)

    # Save to CSV
    pd.DataFrame(results).to_csv(out_csv, index=False)



# test
grid2stat(
        [
            [ "/home/juju/geodata/census/2018/JRC_1K_POP_2018_clean.tif" , 1 ]
        ],
        "/home/juju/Bureau/test.gpkg",
        #"/home/juju/geodata/gisco/NUTS_RG_100K_2024_3035.gpkg",
        "NUTS_ID",
        "/home/juju/Bureau/out.csv",
        out_dict={
            "sum": lambda arr: np.sum([x for x in arr if x is not None]),
            "mean": lambda arr: np.mean([x for x in arr if x is not None]),
            "max": lambda arr: np.max([x for x in arr if x is not None]),
            "min": lambda arr: np.min([x for x in arr if x is not None]),
            "count": lambda arr: len(arr)
        },
        verbose=True
)

