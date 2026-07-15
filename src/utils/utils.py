import numpy as np

def cartesian_product(nb1, nb2):
    pairs = []
    for i in range(nb1 + 1):
        for j in range(nb2 + 1): pairs.append([i, j])
    return pairs


def cartesian_product_comp(minx, miny, maxx, maxy, step=1):
    pairs = []
    for x in range(minx, maxx, step):
        for y in range(miny, maxy, step): pairs.append([x, y])
    return pairs


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    """
    Compute the weighted median of `values`, weighted by `weights`.
    Assumes both are 1D arrays of the same length, already cleaned of nodata.
    """
    if values.size == 0 or weights.sum() == 0:
        return np.nan

    order = np.argsort(values)
    values_sorted = values[order]
    weights_sorted = weights[order]

    cum_weights = np.cumsum(weights_sorted)
    cutoff = weights_sorted.sum() / 2.0

    # first index where cumulative weight reaches half the total weight
    idx = np.searchsorted(cum_weights, cutoff)
    idx = min(idx, len(values_sorted) - 1)  # safety clamp

    return values_sorted[idx]
