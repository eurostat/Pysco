"""
Dependencies
------------
    pip install rasterio geopandas shapely numpy pandas
"""

import csv
from collections import defaultdict
from pathlib import Path

import numpy as np
import numpy.typing as npt
import geopandas as gpd
from typing import Callable

import rasterio
from rasterio.windows import Window
from rasterio.enums import Resampling
from rasterio.transform import from_bounds

from shapely import prepare, contains_xy
from shapely.strtree import STRtree




def aggregate_geotiff_to_regions(
    gpkg_path: str,
    region_id_attr: str,
    geotiff_path: str,
    output_csv_path: str,
    output_col_name: str = "sum",
    block_size: int = 1024,
    band: int = 1,
) -> None:
    """
    For each region in *gpkg_path*, sum the values of all GeoTIFF pixels
    whose centre lies within that region, then write results to a CSV.

    Aggregate GeoTIFF pixel values into polygon regions using a point-in-polygon
    strategy: only the pixel *centres* that fall inside a region are summed.

    Optimisation strategy for large datasets
    -----------------------------------------
    1. Spatial index (STRtree) on the region geometries so pixel-centre lookup is
    O(log n) rather than O(n).
    2. Windowed / block reading of the GeoTIFF – the raster is never loaded
    entirely into RAM.  Each block is read once.
    3. Per-block spatial filter: the block's bounding box is used to pre-filter
    candidate regions before the inner point-in-polygon test.
    4. NumPy vectorised coordinate generation inside each block.
    5. nodata masking applied before any geometry query.
    
    Parameters
    ----------
    gpkg_path : str
        Path to a GeoPackage (.gpkg) containing (multi-)polygon features.
    region_id_attr : str
        Name of the attribute that uniquely identifies each region.
    geotiff_path : str
        Path to the input GeoTIFF (single band used; first band if multi-band).
    output_csv_path : str
        Path for the output CSV file.  Created or overwritten.
    output_col_name : str
        Column name for the aggregated values in the output CSV (default: "sum").
    block_size : int
        Width/height of the processing tile in pixels.  Tune to fit available
        RAM.  1024 is a safe default; raise to 4096+ on memory-rich machines
        for fewer I/O round-trips.
    band : int
        The band number to read from the GeoTIFF (default: 1).
    """
    gpkg_path = Path(gpkg_path)
    geotiff_path = Path(geotiff_path)
    output_csv_path = Path(output_csv_path)

    # ------------------------------------------------------------------
    # 1. Load regions and reproject to the raster CRS
    # ------------------------------------------------------------------
    regions = gpd.read_file(gpkg_path)

    with rasterio.open(geotiff_path) as src:
        raster_crs = src.crs
        transform = src.transform
        nodata = src.nodata
        height, width = src.height, src.width
        #band_count = src.count  # we use band 1

        # Reproject regions if necessary
        if regions.crs is None:
            raise ValueError("GeoPackage has no CRS defined.")
        if regions.crs != raster_crs:
            regions = regions.to_crs(raster_crs)

        # Build a fast spatial index over region geometries
        geom_list = list(regions.geometry)
        id_list = list(regions[region_id_attr])
        tree = STRtree(geom_list)

        # Accumulator: region_id -> running sum
        sums: dict = defaultdict(float)
        # Ensure every region appears in output even if sum == 0
        for rid in id_list:
            sums[rid] = 0.0

        # ------------------------------------------------------------------
        # 2. Tile over the raster
        # ------------------------------------------------------------------
        for row_off in range(0, height, block_size):
            row_count = min(block_size, height - row_off)

            for col_off in range(0, width, block_size):
                col_count = min(block_size, width - col_off)

                window = Window(col_off, row_off, col_count, row_count)
                data = src.read(band, window=window).astype(np.float64)

                # Mask nodata pixels
                if nodata is not None:
                    valid_mask = ~np.isclose(data, nodata)
                else:
                    valid_mask = np.ones(data.shape, dtype=bool)

                # Skip entirely empty blocks
                if not valid_mask.any():
                    continue

                # ------------------------------------------------------
                # 3. Compute pixel-centre coordinates for valid pixels
                # ------------------------------------------------------
                rows_idx, cols_idx = np.where(valid_mask)

                # Absolute pixel indices within the full raster
                abs_rows = rows_idx + row_off
                abs_cols = cols_idx + col_off

                # Pixel centre = top-left corner of raster
                #   + (col + 0.5) * pixel_width
                #   + (row + 0.5) * pixel_height  (negative for north-up)
                xs = transform.c + (abs_cols + 0.5) * transform.a
                ys = transform.f + (abs_rows + 0.5) * transform.e
                values = data[rows_idx, cols_idx]

                # ------------------------------------------------------
                # 4. Bounding-box pre-filter: which regions overlap this
                #    block at all?
                # ------------------------------------------------------
                block_xmin = transform.c + col_off * transform.a
                block_xmax = transform.c + (col_off + col_count) * transform.a
                block_ymax = transform.f + row_off * transform.e
                block_ymin = transform.f + (row_off + row_count) * transform.e
                # Normalise min/max (transform.e is negative for north-up)
                bx_min, bx_max = min(block_xmin, block_xmax), max(block_xmin, block_xmax)
                by_min, by_max = min(block_ymin, block_ymax), max(block_ymin, block_ymax)

                from shapely.geometry import box as shapely_box
                block_box = shapely_box(bx_min, by_min, bx_max, by_max)
                candidate_indices = tree.query(block_box, predicate="intersects")

                if len(candidate_indices) == 0:
                    continue

                candidate_geoms = [geom_list[i] for i in candidate_indices]
                candidate_ids = [id_list[i] for i in candidate_indices]

                # ------------------------------------------------------
                # 5. Point-in-polygon for each candidate region
                # ------------------------------------------------------
                # Build a MultiPoint for bulk contains queries
                #points_xy = np.stack([xs, ys], axis=1)

                for geom, rid in zip(candidate_geoms, candidate_ids):
                    # Fast bounding-box pre-check per region
                    gx_min, gy_min, gx_max, gy_max = geom.bounds
                    in_bbox = (
                        (xs >= gx_min) & (xs <= gx_max) &
                        (ys >= gy_min) & (ys <= gy_max)
                    )
                    if not in_bbox.any():
                        continue

                    bbox_xs = xs[in_bbox]
                    bbox_ys = ys[in_bbox]
                    bbox_vals = values[in_bbox]

                    # Vectorised contains via prepared geometry
                    prepare(geom)
                    inside = contains_xy(geom, bbox_xs, bbox_ys)
                    sums[rid] += bbox_vals[inside].sum()

    # ------------------------------------------------------------------
    # 6. Write CSV
    # ------------------------------------------------------------------
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([region_id_attr, output_col_name])
        for rid in id_list:           # preserve original order
            writer.writerow([rid, sums[rid]])

    print(f"Done. Results written to {output_csv_path}  ({len(id_list)} regions)")



























def transform_geotiff(
    input_path: str,
    output_path: str,
    func: Callable[[npt.NDArray], npt.NDArray],
    output_dtype: str = None,
    band: int = 1,
    compress: str = "lzw",
) -> None:
    """
    Apply a lambda/function to each pixel of a GeoTIFF band and write the result
    to a new GeoTIFF, preserving spatial metadata.
 
    Parameters
    ----------
    input_path : str
        Path to the input GeoTIFF file.
    output_path : str
        Path where the output GeoTIFF will be written.
    func : Callable
        A function (or lambda) applied element-wise to the pixel array.
        Receives a NumPy array and must return a NumPy array of the same shape.
        Example: lambda x: x * 2 + 1
    output_dtype : str, optional
        NumPy/GDAL dtype string for the output raster (e.g. 'float32', 'uint8',
        'int16', 'float64'). Defaults to the input band's dtype when not provided.
    band : int, optional
        1-based band index to read from the input file. Defaults to 1.
 
    Raises
    ------
    ValueError
        If the requested band index is out of range.
    """
    with rasterio.open(input_path) as src:
        data = src.read(band)                          # shape: (height, width)
        profile = src.profile.copy()
 
    # Apply the user-supplied function
    result: npt.NDArray = func(data)
 
    if result.shape != data.shape:
        raise ValueError(
            f"The function returned an array with shape {result.shape}, "
            f"but the input shape is {data.shape}. Shapes must match."
        )
 
    # Resolve output dtype
    resolved_dtype = output_dtype if output_dtype is not None else str(data.dtype)
    result = result.astype(resolved_dtype)

    # Update profile for a single-band output
    profile.update(
        dtype=resolved_dtype,
        count=1,
        compress=compress,
    )
 
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(result, 1)



def multiply_geotiffs(
    path_a: str,
    path_b: str,
    output_path: str,
    band_a: int = 1,
    band_b: int = 1,
    output_dtype: str | None = None,
) -> None:
    """
    Compute the pixel-wise product of two GeoTIFF files and write the result
    to a new GeoTIFF.
    Both inputs must share the same CRS, extent, and pixel grid.
    Where either input pixel is no-data the output pixel is also no-data.
    
    This is usefull to compute weighted average statistics, e.g. population-weighted accessibility:
    1. Multiply an accessibility raster (e.g. travel time to nearest hospital) by a population raster (e.g. population count per pixel).
    2. Sum the resulting "population-weighted accessibility" values within each region.
    3. Divide the total population-weighted accessibility by the total population in that region to get the population-weighted average accessibility.
 
    Parameters
    ----------
    path_a : str
        Path to the first GeoTIFF.
    path_b : str
        Path to the second GeoTIFF.
    output_path : str
        Path for the output GeoTIFF (created or overwritten).
    band_a : int, optional
        1-based band index to read from the first file (default: 1).
    band_b : int, optional
        1-based band index to read from the second file (default: 1).
    output_dtype : str or None, optional
        NumPy/rasterio dtype for the output band, e.g. ``"float32"``.
        Defaults to ``float64`` so that integer products don't overflow.
    """
    with rasterio.open(path_a) as src_a, rasterio.open(path_b) as src_b:
 
        # ------------------------------------------------------------------ #
        # Read data and no-data values                                        #
        # ------------------------------------------------------------------ #
        data_a = src_a.read(band_a).astype(np.float64)
        data_b = src_b.read(band_b).astype(np.float64)
 
        nodata_a = src_a.nodata
        nodata_b = src_b.nodata
 
        # ------------------------------------------------------------------ #
        # Build no-data masks (True where the pixel IS no-data)              #
        # ------------------------------------------------------------------ #
        if nodata_a is not None and np.isnan(nodata_a):
            mask_a = np.isnan(data_a)
        elif nodata_a is not None:
            mask_a = data_a == nodata_a
        else:
            mask_a = np.zeros(data_a.shape, dtype=bool)
 
        if nodata_b is not None and np.isnan(nodata_b):
            mask_b = np.isnan(data_b)
        elif nodata_b is not None:
            mask_b = data_b == nodata_b
        else:
            mask_b = np.zeros(data_b.shape, dtype=bool)
 
        combined_nodata_mask = mask_a | mask_b
 
        # ------------------------------------------------------------------ #
        # Compute product                                                     #
        # ------------------------------------------------------------------ #
        product = data_a * data_b
 
        # ------------------------------------------------------------------ #
        # Choose output dtype and no-data sentinel                           #
        # ------------------------------------------------------------------ #
        if output_dtype is None:
            output_dtype = "float64"
 
        # Use NaN as the output no-data sentinel for float types; fall back
        # to the first file's no-data value (or -9999) for integer types.
        np_dtype = np.dtype(output_dtype)
        if np.issubdtype(np_dtype, np.floating):
            out_nodata = float("nan")
        else:
            # For integer outputs pick a sentinel: prefer source A's value
            out_nodata = nodata_a if nodata_a is not None else -9999
            out_nodata = int(out_nodata)
 
        product = product.astype(np_dtype)
        product[combined_nodata_mask] = out_nodata
 
        # ------------------------------------------------------------------ #
        # Write output GeoTIFF (copy spatial metadata from file A)          #
        # ------------------------------------------------------------------ #
        profile = src_a.profile.copy()
        profile.update(
            dtype=output_dtype,
            count=1,
            nodata=out_nodata,
            compress="lzw",          # lossless, widely supported
            predictor=2,             # horizontal differencing – good for floats
            tiled=True,
            blockxsize=256,
            blockysize=256,
        )
 
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(product[np.newaxis, :, :])   # shape (1, rows, cols)
 
