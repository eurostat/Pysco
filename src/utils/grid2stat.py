"""
Raster -> region statistics.

Two public functions:

* ``grid2stat_threshold``        sum of a raster (e.g. population) per region, optionally split by mask classes
* ``grid2stat_weighted_average`` weighted average + weighted median of an indicator raster per region

Design notes (memory / correctness)
-----------------------------------
* Every region is processed through its own *bounding window*, and that window is read in
  horizontal strips of at most ``chunk_pixels`` pixels. Peak memory is therefore bounded by the
  strip size, not by the size of the largest region.
* The in-polygon mask is rasterised strip by strip (``geometry_mask``), so no full-window
  boolean array is ever allocated. A pixel belongs to a region if its *centre* is inside it.
* Regions are processed independently, so overlapping / nested regions are handled correctly.
* All files are opened through a single ``ExitStack`` and closed even if opening one of them fails.
* The GDAL block cache is capped (``gdal_cache_mb``).
* Nodata is taken from the dataset mask (``read(masked=True)``), which works for integer,
  unsigned and float rasters, with or without a declared nodata value, and for NaN nodata.
  Non-finite values in float rasters are always treated as invalid.

IMPORTANT for mask functions: they are applied to one strip at a time, so they must be
element-wise (e.g. ``lambda a: a == 21``, ``lambda a: (a >= 10) & (a < 20)``). A function that
uses statistics of the whole array (``a > a.mean()``) would give strip-dependent results.
"""
from __future__ import annotations

import logging
import math
from contextlib import ExitStack, nullcontext
from itertools import product
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import Window
from rasterio.windows import transform as window_transform
from shapely.geometry import MultiPolygon, box, mapping
from shapely.validation import make_valid

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_PIXELS = 4_000_000   # ~32 MB per float64 array
DEFAULT_GDAL_CACHE_MB = 512

_RESERVED_COLUMNS = {"VALUE", "STATINFO"}


# =============================================================================
# Public API
# =============================================================================

def grid2stat_threshold(
    population_path: str,
    population_band: int = 1,

    region_path=None,
    region_id_att: str = "id",
    region_filter: Optional[Callable] = None,

    masks: Optional[list] = None,

    value_when_no_population=0,

    *,
    keep_uncovered_regions: bool = True,
    strict: bool = True,
    chunk_pixels: int = DEFAULT_CHUNK_PIXELS,
    gdal_cache_mb: Optional[int] = DEFAULT_GDAL_CACHE_MB,
) -> pd.DataFrame:
    """
    Sum of raster values per region: the sum of all valid cells whose centre lies within the region.
    Optionally split by masks (e.g. degurba level, CLC class, ...).

    Args:
        population_path:   Path to the population raster.
        population_band:   1-based band to read.
        region_path:       Path to the regions vector file (or an already loaded GeoDataFrame).
        region_id_att:     Attribute holding the region identifier.
        region_filter:     Optional callable(row) -> bool selecting the regions to process.
        masks:             List of dicts, each with:
                             'path'     : mask raster (same grid as the population raster)
                             'fun'      : {label: callable(array) -> boolean array (True = keep) | None}
                                          (None, or a function returning None, means "no filtering")
                             'dim_name' : output column holding the label
                             'band'     : optional, 1-based band (default 1)
                             'coeff'    : optional, the mask array is multiplied by it before the
                                          functions are called (default: no scaling)
        value_when_no_population: value used when a (region, configuration) has no valid cell.
        keep_uncovered_regions: if True (default), regions that do not overlap the raster still
                           produce rows with ``value_when_no_population``, consistent with
                           regions that overlap but have no valid cell. If False they are omitted.
        strict:            if True (default) any unexpected error on a region is raised.
                           If False, the region is logged, skipped and listed in
                           ``df.attrs["failed_regions"]``.
        chunk_pixels:      maximum number of pixels read at once (memory / speed trade-off).
        gdal_cache_mb:     GDAL block cache limit in MB (None = leave GDAL default).

    Returns:
        DataFrame with one row per (region, mask-label combination), columns
        ``[region_id_att, 'VALUE', *dim_names]``. ``df.attrs`` contains ``dropped_regions``
        (unusable geometries) and ``failed_regions`` (errors when ``strict=False``).
    """
    masks = _normalise_masks(masks, region_id_att)
    configurations = _build_configurations(masks)
    _check_chunk_pixels(chunk_pixels)

    out: List[dict] = []
    failed: List[Any] = []

    with ExitStack() as stack:
        stack.enter_context(_gdal_env(gdal_cache_mb))
        src_pop = stack.enter_context(rasterio.open(population_path))
        src_masks = [stack.enter_context(rasterio.open(m["path"])) for m in masks]

        _validate_rasters(src_pop, src_masks)
        _check_band(src_pop, population_band, "population")
        for sm, m in zip(src_masks, masks):
            _check_band(sm, m["band"], f"mask '{m['dim_name']}'")

        regions, dropped = _load_regions(region_path, region_id_att, region_filter, src_pop.crs)
        raster_box = box(*src_pop.bounds)

        for region_id, geom in zip(regions[region_id_att], regions.geometry):
            try:
                covered = geom.intersects(raster_box)
                if not covered and not keep_uncovered_regions:
                    continue

                if covered:
                    totals, counts = _sum_region(
                        src_pop, population_band, src_masks, masks, configurations, geom, chunk_pixels
                    )
                else:
                    totals, counts = {}, {}

                for conf in configurations:
                    n = counts.get(conf, 0)
                    value = totals[conf] if n > 0 else value_when_no_population
                    row = {region_id_att: region_id, "VALUE": value}
                    row.update({m["dim_name"]: conf[i] for i, m in enumerate(masks)})
                    out.append(row)

            except Exception as exc:  # noqa: BLE001 - deliberate, see `strict`
                _handle_region_failure(strict, region_id, exc, failed)

    columns = [region_id_att, "VALUE"] + [m["dim_name"] for m in masks]
    df = pd.DataFrame(out, columns=columns)
    df.attrs["dropped_regions"] = dropped
    df.attrs["failed_regions"] = failed
    _log_summary("grid2stat_threshold", dropped, failed)
    return df


def grid2stat_weighted_average(
    indic_path: str,
    weight_path: str,
    indic_band: int = 1,
    weight_band: int = 1,
    region_path=None,
    region_id_att: str = "id",
    region_filter: Optional[Callable] = None,
    masks: Optional[list] = None,

    *,
    compute_median: bool = True,
    keep_uncovered_regions: bool = True,
    strict: bool = True,
    chunk_pixels: int = DEFAULT_CHUNK_PIXELS,
    gdal_cache_mb: Optional[int] = DEFAULT_GDAL_CACHE_MB,
) -> pd.DataFrame:
    """
    Weighted average (STATINFO='AVG') and weighted median (STATINFO='MED') of an indicator raster
    per region, using a weight raster (e.g. population). Masks are applied to both identically.

    A cell is used if its centre is in the region, indicator and weight are both valid
    (not nodata, finite) and weight >= 0.

    Args:
        indic_path, indic_band:   indicator raster and 1-based band.
        weight_path, weight_band: weight raster and 1-based band (same grid as the indicator).
        region_path, region_id_att, region_filter, masks: see ``grid2stat_threshold``.
        compute_median:    set False to skip the median. The median needs the valid values of a
                           region in memory (strip-wise accumulation, then one sort), so on very
                           large regions with many mask configurations it is the memory hot spot.
        keep_uncovered_regions: if True (default), regions that do not overlap the raster or
                           have no valid cell yield NaN rows (same as empty configurations
                           already did). If False they are omitted.
        strict, chunk_pixels, gdal_cache_mb: see ``grid2stat_threshold``.

    Returns:
        DataFrame with columns ``[region_id_att, 'STATINFO', 'VALUE', *dim_names]``, with one
        'AVG' row (and one 'MED' row if requested) per (region, mask-label combination).
    """
    masks = _normalise_masks(masks, region_id_att)
    configurations = _build_configurations(masks)
    _check_chunk_pixels(chunk_pixels)

    out: List[dict] = []
    failed: List[Any] = []

    def make_row(region_id, value, stat, conf):
        row = {region_id_att: region_id, "STATINFO": stat, "VALUE": value}
        for i, m in enumerate(masks):
            row[m["dim_name"]] = conf[i]
        return row

    with ExitStack() as stack:
        stack.enter_context(_gdal_env(gdal_cache_mb))
        src_indic = stack.enter_context(rasterio.open(indic_path))
        src_weight = stack.enter_context(rasterio.open(weight_path))
        src_masks = [stack.enter_context(rasterio.open(m["path"])) for m in masks]

        _validate_rasters(src_indic, [src_weight] + src_masks)
        _check_band(src_indic, indic_band, "indicator")
        _check_band(src_weight, weight_band, "weight")
        for sm, m in zip(src_masks, masks):
            _check_band(sm, m["band"], f"mask '{m['dim_name']}'")

        regions, dropped = _load_regions(region_path, region_id_att, region_filter, src_indic.crs)
        raster_box = box(*src_indic.bounds)

        for region_id, geom in zip(regions[region_id_att], regions.geometry):
            try:
                covered = geom.intersects(raster_box)
                if not covered and not keep_uncovered_regions:
                    continue

                if covered:
                    accs, any_valid = _weighted_region(
                        src_indic, indic_band, src_weight, weight_band, src_masks, masks,
                        configurations, geom, chunk_pixels, compute_median,
                    )
                else:
                    accs, any_valid = None, False

                if not any_valid and not keep_uncovered_regions:
                    continue

                for conf in configurations:
                    wa, wmed = accs[conf].result() if accs is not None else (np.nan, np.nan)
                    out.append(make_row(region_id, wa, "AVG", conf))
                    if compute_median:
                        out.append(make_row(region_id, wmed, "MED", conf))
                accs = None  # release samples before the next region

            except Exception as exc:  # noqa: BLE001 - deliberate, see `strict`
                _handle_region_failure(strict, region_id, exc, failed)

    columns = [region_id_att, "STATINFO", "VALUE"] + [m["dim_name"] for m in masks]
    df = pd.DataFrame(out, columns=columns)
    df.attrs["dropped_regions"] = dropped
    df.attrs["failed_regions"] = failed
    _log_summary("grid2stat_weighted_average", dropped, failed)
    return df


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    """Weighted median: smallest value whose cumulative weight reaches half the total weight."""
    if values.size == 0:
        return float("nan")
    order = np.argsort(values, kind="stable")
    v, w = values[order], weights[order]
    cum = np.cumsum(w)
    total = cum[-1]
    if not total > 0:
        return float("nan")
    idx = int(np.searchsorted(cum, 0.5 * total))
    return float(v[min(idx, v.size - 1)])


# =============================================================================
# Per-region computation
# =============================================================================

def _sum_region(src_pop, band, src_masks, masks, configurations, geom, chunk_pixels):
    """Strip-wise sums per mask configuration. Returns (totals, counts) dicts keyed by conf."""
    totals = dict.fromkeys(configurations, 0.0)
    counts = dict.fromkeys(configurations, 0)

    for window, inside in _iter_region_chunks(src_pop, geom, chunk_pixels):
        data, valid = _read_valid(src_pop, band, window)
        valid &= inside
        if not valid.any():
            continue

        evaluated = _evaluate_mask_functions(masks, _read_mask_arrays(src_masks, masks, window))

        for conf in configurations:
            combined = _combine_masks(conf, evaluated)
            sel = valid if combined is None else (valid & combined)
            n = int(np.count_nonzero(sel))
            if n:
                # `where=` avoids building the intermediate data[sel] array; float64 accumulator
                totals[conf] += float(data.sum(where=sel, dtype=np.float64))
                counts[conf] += n

    return totals, counts


class _WeightedAccumulator:
    """Accumulates sum(w), sum(w*x) and (optionally) the samples needed for the weighted median."""

    __slots__ = ("n", "sum_w", "sum_iw", "keep_samples", "_values", "_weights")

    def __init__(self, keep_samples: bool):
        self.n = 0
        self.sum_w = 0.0
        self.sum_iw = 0.0
        self.keep_samples = keep_samples
        self._values: List[np.ndarray] = []
        self._weights: List[np.ndarray] = []

    def add(self, ind: np.ndarray, w: np.ndarray) -> None:
        self.n += int(ind.size)
        self.sum_w += float(w.sum())
        self.sum_iw += float((ind * w).sum())
        if self.keep_samples:
            pos = w > 0          # zero-weight cells never change a weighted median
            if pos.any():
                self._values.append(ind[pos])
                self._weights.append(w[pos])

    def result(self) -> Tuple[float, float]:
        if self.n == 0 or not self.sum_w > 0:
            return np.nan, np.nan
        wa = self.sum_iw / self.sum_w
        if not self.keep_samples:
            return wa, np.nan
        wmed = weighted_median(np.concatenate(self._values), np.concatenate(self._weights))
        return wa, wmed


def _weighted_region(src_indic, indic_band, src_weight, weight_band, src_masks, masks,
                     configurations, geom, chunk_pixels, compute_median):
    """Strip-wise accumulation per mask configuration. Returns (accumulators, any_valid_cell)."""
    accs = {conf: _WeightedAccumulator(compute_median) for conf in configurations}
    any_valid = False

    for window, inside in _iter_region_chunks(src_indic, geom, chunk_pixels):
        ind_data, valid = _read_valid(src_indic, indic_band, window)
        w_data, w_valid = _read_valid(src_weight, weight_band, window)
        valid &= w_valid
        valid &= inside
        del w_valid, inside
        with np.errstate(invalid="ignore"):
            valid &= (w_data >= 0)
        if not valid.any():
            continue
        any_valid = True

        evaluated = _evaluate_mask_functions(masks, _read_mask_arrays(src_masks, masks, window))

        for conf in configurations:
            combined = _combine_masks(conf, evaluated)
            sel = valid if combined is None else (valid & combined)
            if not sel.any():
                continue
            ind = ind_data[sel].astype(np.float64, copy=False)
            w = w_data[sel].astype(np.float64, copy=False)
            accs[conf].add(ind, w)

    return accs, any_valid


# =============================================================================
# Raster helpers
# =============================================================================

def _gdal_env(gdal_cache_mb: Optional[int]):
    if gdal_cache_mb is None:
        return nullcontext()
    return rasterio.Env(GDAL_CACHEMAX=int(gdal_cache_mb))


def _validate_rasters(ref, others: Sequence) -> None:
    """Check that all rasters share exactly the same grid as the reference raster."""
    ref_t = tuple(ref.transform)[:6]
    for s in others:
        if s.crs != ref.crs:
            raise ValueError(f"CRS mismatch: {ref.name} ({ref.crs}) vs {s.name} ({s.crs})")
        if (s.width, s.height) != (ref.width, ref.height):
            raise ValueError(
                f"Shape mismatch: {ref.name} {(ref.width, ref.height)} vs {s.name} {(s.width, s.height)}"
            )
        if not np.allclose(tuple(s.transform)[:6], ref_t, rtol=1e-9, atol=1e-12):
            raise ValueError(f"Transform mismatch: {ref.name} {ref.transform} vs {s.name} {s.transform}")


def _check_band(src, band, label: str) -> None:
    if not isinstance(band, (int, np.integer)) or isinstance(band, bool) or not 1 <= band <= src.count:
        raise ValueError(f"Invalid {label} band {band!r}: '{src.name}' has {src.count} band(s) (1-based).")


def _check_chunk_pixels(chunk_pixels) -> None:
    if not isinstance(chunk_pixels, (int, np.integer)) or chunk_pixels < 1:
        raise ValueError("chunk_pixels must be a positive integer.")


def _region_window(src, geom) -> Optional[Window]:
    """Smallest whole-pixel window of ``src`` containing the bounds of ``geom`` (None if outside)."""
    minx, miny, maxx, maxy = geom.bounds
    inv = ~src.transform
    corners = [inv * (x, y) for x, y in ((minx, miny), (minx, maxy), (maxx, miny), (maxx, maxy))]
    cols = [c[0] for c in corners]
    rows = [c[1] for c in corners]
    col0 = max(int(math.floor(min(cols))), 0)
    col1 = min(int(math.ceil(max(cols))), src.width)
    row0 = max(int(math.floor(min(rows))), 0)
    row1 = min(int(math.ceil(max(rows))), src.height)
    if col1 <= col0 or row1 <= row0:
        return None
    return Window(col0, row0, col1 - col0, row1 - row0)


def _iter_region_chunks(ref, geom, chunk_pixels: int) -> Iterator[Tuple[Window, np.ndarray]]:
    """
    Yield ``(window, inside)`` for horizontal strips covering the region.
    ``inside`` is True where the pixel centre lies within the geometry. Strips with no pixel
    inside are skipped, so nothing is read for them.
    """
    window = _region_window(ref, geom)
    if window is None:
        return
    width, height = int(window.width), int(window.height)
    rows_per_chunk = max(1, int(chunk_pixels) // max(width, 1))
    shapes = [mapping(geom)]

    for r0 in range(0, height, rows_per_chunk):
        nrows = min(rows_per_chunk, height - r0)
        sub = Window(int(window.col_off), int(window.row_off) + r0, width, nrows)
        inside = geometry_mask(
            shapes,
            out_shape=(nrows, width),
            transform=window_transform(sub, ref.transform),
            all_touched=False,
            invert=True,
        )
        if inside.any():
            yield sub, inside


def _read_valid(src, band: int, window: Window) -> Tuple[np.ndarray, np.ndarray]:
    """Read a window; return (data, valid) where valid excludes nodata and non-finite floats."""
    arr = src.read(band, window=window, masked=True)
    data = np.ma.getdata(arr)
    valid = ~np.ma.getmaskarray(arr)          # always a fresh, writable array
    if np.issubdtype(data.dtype, np.floating):
        valid &= np.isfinite(data)
    return data, valid


def _read_mask_arrays(src_masks, masks, window: Window) -> List[np.ndarray]:
    """Raw mask values (no nodata masking: the mask functions decide what to keep)."""
    return [sm.read(m["band"], window=window) for sm, m in zip(src_masks, masks)]


# =============================================================================
# Mask helpers
# =============================================================================

def _normalise_masks(masks: Optional[list], region_id_att: str) -> List[dict]:
    """Validate the mask specs and return shallow copies (the caller's dicts are never modified)."""
    out: List[dict] = []
    names = set()
    for i, m in enumerate(masks or []):
        missing = {"path", "fun", "dim_name"} - set(m)
        if missing:
            raise ValueError(f"masks[{i}] is missing key(s): {sorted(missing)}")
        if not isinstance(m["fun"], dict) or not m["fun"]:
            raise ValueError(f"masks[{i}]['fun'] must be a non-empty dict {{label: callable | None}}")
        name = m["dim_name"]
        if name in names:
            raise ValueError(f"Duplicate mask dim_name {name!r}")
        if name == region_id_att or name in _RESERVED_COLUMNS:
            raise ValueError(f"mask dim_name {name!r} clashes with an output column")
        names.add(name)
        mm = dict(m)
        mm["band"] = m.get("band") or 1
        out.append(mm)
    return out


def _build_configurations(masks: List[dict]) -> List[tuple]:
    """Cartesian product of all mask labels: one output item per configuration and region."""
    return list(product(*(m["fun"].keys() for m in masks))) if masks else [()]


def _evaluate_mask_functions(masks: List[dict], mask_arrays: List[np.ndarray]) -> List[dict]:
    """
    Evaluate every mask function exactly once per strip (instead of once per configuration).
    Returns, for each mask, ``{label: boolean array | None}`` (None = no filtering).
    """
    evaluated: List[dict] = []
    for m, arr in zip(masks, mask_arrays):
        coeff = m.get("coeff")
        scaled = arr if (coeff is None or coeff == 1) else coeff * arr   # no copy when no scaling
        per_label: Dict[Any, Optional[np.ndarray]] = {}
        for label, fn in m["fun"].items():
            res = None if fn is None else fn(scaled)
            if res is not None:
                res = np.asarray(res, dtype=bool)
                if res.shape != arr.shape:
                    raise ValueError(
                        f"mask '{m['dim_name']}', label {label!r}: function returned shape "
                        f"{res.shape}, expected {arr.shape}"
                    )
            per_label[label] = res
        evaluated.append(per_label)
    return evaluated


def _combine_masks(conf: tuple, evaluated: List[dict]) -> Optional[np.ndarray]:
    """AND of the pre-evaluated masks for one configuration (None = keep everything)."""
    combined = None
    for label, per_label in zip(conf, evaluated):
        res = per_label[label]
        if res is None:
            continue
        combined = res if combined is None else (combined & res)
    return combined


# =============================================================================
# Region helpers
# =============================================================================

def _load_regions(region_path, region_id_att: str, region_filter, target_crs):
    """
    Load, filter, reproject to the raster CRS and clean the region geometries.
    Returns ``(GeoDataFrame[id, geometry], dropped_ids)``.
    """
    if region_path is None:
        raise ValueError("region_path is required.")
    regions = region_path.copy() if isinstance(region_path, gpd.GeoDataFrame) else gpd.read_file(region_path)

    if region_id_att not in regions.columns:
        raise ValueError(f"Region attribute {region_id_att!r} not found. Available: {list(regions.columns)}")

    if region_filter is not None and not regions.empty:
        regions = regions[regions.apply(region_filter, axis=1).astype(bool)]

    geom_col = regions.geometry.name
    if region_id_att == geom_col:
        raise ValueError("region_id_att cannot be the geometry column.")
    regions = regions[[region_id_att, geom_col]]
    if regions.empty:
        raise ValueError("No regions found after filtering.")

    # Reproject to the raster CRS
    if target_crs is not None:
        if regions.crs is None:
            logger.warning("Region file has no CRS; assuming it is already in the raster CRS (%s).", target_crs)
        elif regions.crs != target_crs:
            regions = regions.to_crs(target_crs)

    # Clean geometries: None / empty dropped, invalid repaired, only polygonal parts kept
    fixed = [_fix_geometry(g) for g in regions.geometry]
    keep = np.array([g is not None for g in fixed], dtype=bool)
    dropped = regions.loc[~keep, region_id_att].tolist()
    if dropped:
        logger.warning("%d region(s) dropped (empty/invalid/non-polygonal geometry): %s",
                       len(dropped), _preview(dropped))
    regions = regions.loc[keep].copy()
    regions[geom_col] = gpd.GeoSeries([g for g in fixed if g is not None], index=regions.index, crs=regions.crs)

    if regions.empty:
        raise ValueError("No usable region geometry left after cleaning.")

    dup = regions[region_id_att][regions[region_id_att].duplicated()].unique().tolist()
    if dup:
        logger.warning("Duplicate region ids (their rows will be repeated in the output): %s", _preview(dup))

    return regions, dropped


def _polygonal_part(geom):
    """Keep only the polygonal content of a geometry (None if there is none)."""
    if geom is None or geom.is_empty:
        return None
    if geom.geom_type in ("Polygon", "MultiPolygon"):
        return geom
    if geom.geom_type == "GeometryCollection":
        polys = []
        for g in geom.geoms:
            p = _polygonal_part(g)
            if p is not None:
                polys.extend(p.geoms if p.geom_type == "MultiPolygon" else [p])
        return MultiPolygon(polys) if polys else None
    return None


def _fix_geometry(geom):
    if geom is None or geom.is_empty:
        return None
    if not geom.is_valid:
        geom = make_valid(geom)
    return _polygonal_part(geom)


# =============================================================================
# Misc
# =============================================================================

def _handle_region_failure(strict: bool, region_id, exc: Exception, failed: list) -> None:
    if strict:
        raise RuntimeError(f"Processing failed for region {region_id!r}: {exc}") from exc
    logger.exception("[%s] processing failed, region skipped", region_id)
    failed.append(region_id)


def _preview(items: list, n: int = 10) -> str:
    s = ", ".join(map(str, items[:n]))
    return s + (f", ... (+{len(items) - n} more)" if len(items) > n else "")


def _log_summary(name: str, dropped: list, failed: list) -> None:
    if dropped or failed:
        logger.warning("%s: %d dropped region(s), %d failed region(s)%s",
                       name, len(dropped), len(failed),
                       f" (failed: {_preview(failed)})" if failed else "")
