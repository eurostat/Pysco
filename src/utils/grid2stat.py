import rasterio
import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio.mask import mask,raster_geometry_mask
from shapely.geometry import mapping
from typing import Dict
from itertools import product
from contextlib import ExitStack

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.utils import weighted_median



def grid2stat_threshold(
    population_path: str,
    population_band: int = 1,

    region_path: str = None,
    region_id_att: str = "id",
    region_filter=None,

    masks: list = None,

    value_when_no_population=0,
) -> pd.DataFrame:
    """
    Compute population statistics per region. It is the sum of the geotiff values for all the cells whose centre lies within the region.
    It can optionaly apply various masks to compute statistics, for example, by degurba level 2, by CLC class, etc.

    Args:
        population_path:        Path to the population raster file.
        population_band:        Band index (1-based) to read from the population raster.
        region_path:            Path to the regions vector file.
        region_id_att:          Attribute name used as region identifier.
        region_filter:          Optional callable(row) -> bool to filter regions.
        masks:                  List of mask dicts with keys: 'path', 'band', 'fun', 'dim_name'.
        value_when_no_population: Value to use when no population pixels are found.

    Returns:
        DataFrame with one row per (region, mask configuration).
    """
    if masks is None:
        masks = []

    # Load and optionally filter regions
    regions = gpd.read_file(region_path)
    if region_filter:
        regions = regions[regions.apply(region_filter, axis=1)]
    regions = regions[[region_id_att, "geometry"]]

    if regions.empty:
        raise ValueError("No regions found after filtering.")

    # Precompute cartesian product of all mask configurations
    # One stat value item will be produced for each of these configurations, for each region
    configurations = list(product(*(m["fun"].keys() for m in masks))) if masks else [()]

    out = []
    with ExitStack() as stack:
        # Open rasters: population and masks
        src_population = stack.enter_context(rasterio.open(population_path))
        src_masks = [stack.enter_context(rasterio.open(m["path"])) for m in masks]

        # Check rasters are compatible
        _validate_rasters(src_population, src_masks)

        # Reproject regions to raster CRS if needed
        if regions.crs is not None and src_population.crs is not None and regions.crs != src_population.crs:
            regions = regions.to_crs(src_population.crs)

        # Set no data value for population
        population_nodata = src_population.nodata if src_population.nodata is not None else -9999

        # Process each region
        for _, region in regions.iterrows():

            # get region id and geometry
            region_id = region[region_id_att]
            #if region_id != "AT001F": continue  # DEBUG: skip all but one region
            geometry = [mapping(region.geometry)]

            # Clip rasters to region geometry
            try:
                pop_clipped, mask_clipped = _clip_rasters( src_population, src_masks, masks, geometry,population_band, population_nodata)
            except SkipRegion: continue
            except Exception as e:
                print(f"[{region_id}] Clipping failed: {e}")
                continue

            # handle each mask configuration
            for conf in configurations:

                # get boolean mask
                combined_mask = _build_combined_mask(conf, masks, mask_clipped)

                # apply mask on population data
                pop = pop_clipped if combined_mask is None else pop_clipped[combined_mask]
                pop = pop[pop != population_nodata]

                # make data item
                row = {region_id_att: region_id}
                row["VALUE"] = pop.sum() if pop.size > 0 else value_when_no_population
                for i, m in enumerate(masks):
                    row[m["dim_name"]] = conf[i]
                out.append(row)

    return pd.DataFrame(out)




def grid2stat_weighted_average(
    indic_path: str,
    weight_path: str,
    indic_band: int = 1,
    weight_band: int = 1,
    region_path: str = None,
    region_id_att: str = "id",
    region_filter=None,
    masks: list = None,
) -> pd.DataFrame:
    """
    Compute weighted average and weighted median of an indicator raster over regions,
    using a weight raster (e.g. population). Masks are applied identically to both.

    masks: list of dicts with keys:
        'path'     : mask raster path (same grid as indicator/weight)
        'band'     : 1-based band index
        'fun'      : dict {label: callable(array) -> boolean array (True = keep) or None}
        'dim_name' : output column name holding the label
    """
    masks = masks or []

    # Load / filter regions
    regions = gpd.read_file(region_path)
    if region_filter:
        regions = regions[regions.apply(region_filter, axis=1)]
    regions = regions[[region_id_att, "geometry"]]
    if regions.empty:
        raise ValueError("No regions found after filtering.")

    # One output item per combination of mask labels, per region
    configurations = list(product(*(m["fun"].keys() for m in masks))) if masks else [()]

    def make_row(region_id, value, indic_type, conf):
        row = {region_id_att: region_id, "STATINFO": indic_type, "VALUE": value}
        for i, m in enumerate(masks):
            row[m["dim_name"]] = conf[i]
        return row

    out = []
    with ExitStack() as stack:
        src_indic = stack.enter_context(rasterio.open(indic_path))
        src_weight = stack.enter_context(rasterio.open(weight_path))
        src_masks = [stack.enter_context(rasterio.open(m["path"])) for m in masks]

        _validate_rasters(src_indic, [src_weight] + src_masks)

        # Reproject regions to raster CRS if needed
        if regions.crs is not None and src_indic.crs is not None and regions.crs != src_indic.crs:
            regions = regions.to_crs(src_indic.crs)

        for _, region in regions.iterrows():
            region_id = region[region_id_att]
            #if region_id != "AT001F": continue  # DEBUG: skip all but one region
            #print(f"[{region_id}] Processing region...")
            geometry = [mapping(region.geometry)]

            try:
                # shape_mask: True OUTSIDE the geometry; window: crop window (same grid for all rasters)
                shape_mask, _, window = raster_geometry_mask(src_indic, geometry, crop=True)

                # masked=True -> nodata pixels are masked automatically
                indic_arr = src_indic.read(indic_band, window=window, masked=True)
                weight_arr = src_weight.read(weight_band, window=window, masked=True)
                mask_arrays = [
                    sm.read(m["band"], window=window)
                    for sm, m in zip(src_masks, masks)
                ]
            except ValueError:
                # typically "Input shapes do not overlap raster"
                continue
            except Exception as e:
                print(f"[{region_id}] Clipping failed: {e}")
                continue

            # Base validity: inside polygon, not nodata, finite, non-negative weight
            indic_f = indic_arr.astype("float64").filled(np.nan)
            weight_f = weight_arr.astype("float64").filled(np.nan)
            base_valid = (
                ~shape_mask
                & np.isfinite(indic_f)
                & np.isfinite(weight_f)
                & (weight_f >= 0)
            )
            if not base_valid.any():
                continue

            for conf in configurations:
                combined = _build_combined_mask(conf, masks, mask_arrays)
                valid = base_valid if combined is None else (base_valid & combined)

                indic = indic_f[valid]
                weight = weight_f[valid]

                if indic.size == 0 or weight.sum() <= 0:
                    wa, wmed = np.nan, np.nan
                else:
                    wa = float((indic * weight).sum() / weight.sum())
                    wmed = weighted_median(indic, weight)

                out.append(make_row(region_id, wa, "AVG", conf))
                out.append(make_row(region_id, wmed, "MED", conf))

                #print(f"[{region_id}]: WA={wa}, WM={wmed}")

    return pd.DataFrame(out)





class SkipRegion(Exception):
    """Raised when a region has no valid data and should be silently skipped."""



def _validate_rasters(ref, others: list) -> None:
    """Check that all rasters share the same grid as the reference raster."""
    for s in others:
        if s.crs != ref.crs:
            raise ValueError(f"CRS mismatch: {ref.crs} vs {s.crs}")
        if s.transform != ref.transform:
            raise ValueError(f"Transform mismatch: {ref.transform} vs {s.transform}")
        if s.res != ref.res:
            raise ValueError(f"Resolution mismatch: {ref.res} vs {s.res}")
        if (s.width, s.height) != (ref.width, ref.height):
            raise ValueError(f"Shape mismatch: {(ref.width, ref.height)} vs {(s.width, s.height)}")



def _clip_rasters(src_population, src_masks, masks, geometry, population_band, population_nodata):
    """Clip population and mask rasters to a region geometry."""
    try:
        pop_clipped = mask(src_population, geometry, crop=True, filled=True, nodata=population_nodata)[0][population_band - 1]
        mask_clipped = [
            mask(sm, geometry, crop=True, filled=True)[0][m["band"] - 1]
            for sm, m in zip(src_masks, masks)
        ]
    except ValueError: raise SkipRegion()

    return pop_clipped, mask_clipped


def _build_combined_mask(conf, masks, mask_arrays):
    """Combine individual mask functions into a single boolean mask (True = keep)."""
    combined = None
    for i, (key, m) in enumerate(zip(conf, masks)):
        mf = m["fun"].get(key)
        if mf is None:
            continue
        c = m.get("coeff")
        if c is None: c = 1.0
        res = mf(c * mask_arrays[i])
        if res is None:
            continue
        res = np.asarray(res, dtype=bool)
        combined = res if combined is None else (combined & res)
    return combined

