"""
aggregate_geotiff.py
--------------------
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

Dependencies
------------
    pip install rasterio geopandas shapely numpy pandas
"""

import csv
from collections import defaultdict
from pathlib import Path

import numpy as np
import geopandas as gpd
import rasterio
from rasterio.windows import Window
from shapely.geometry import MultiPoint
from shapely.strtree import STRtree


def aggregate_geotiff_to_regions(
    gpkg_path: str,
    region_id_attr: str,
    geotiff_path: str,
    output_csv_path: str,
    block_size: int = 1024,
) -> None:
    """
    For each region in *gpkg_path*, sum the values of all GeoTIFF pixels
    whose centre lies within that region, then write results to a CSV.

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
    block_size : int
        Width/height of the processing tile in pixels.  Tune to fit available
        RAM.  1024 is a safe default; raise to 4096+ on memory-rich machines
        for fewer I/O round-trips.
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
        band_count = src.count  # we use band 1

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
                data = src.read(1, window=window).astype(np.float64)

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
                points_xy = np.stack([xs, ys], axis=1)

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
                    from shapely import prepare, contains_xy
                    prepare(geom)
                    inside = contains_xy(geom, bbox_xs, bbox_ys)
                    sums[rid] += bbox_vals[inside].sum()

    # ------------------------------------------------------------------
    # 6. Write CSV
    # ------------------------------------------------------------------
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([region_id_attr, "sum"])
        for rid in id_list:           # preserve original order
            writer.writerow([rid, sums[rid]])

    print(f"Done. Results written to {output_csv_path}  ({len(id_list)} regions)")

