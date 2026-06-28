import rasterio
import geopandas as gpd
import pandas as pd
from rasterio.mask import mask
from shapely.geometry import mapping
from typing import Dict
from itertools import product


def grid2stat(
    population_path: str,
    population_band: int = 1,

    region_path: str = None,
    region_id_att: str = "id",
    region_filter=None,

    masks: list = None,

    value_when_no_population=0,
) -> pd.DataFrame:
    """
    Compute population statistics per region and mask configuration.

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

    # --- Load and optionally filter regions ---
    regions = gpd.read_file(region_path)
    if region_filter:
        regions = regions[regions.apply(region_filter, axis=1)]
    regions = regions[[region_id_att, "geometry"]]

    if regions.empty:
        raise ValueError("No regions found after filtering.")

    # Precompute cartesian product of all mask configurations
    configurations = list(product(*(m["fun"].keys() for m in masks))) if masks else [()]

    out = []

    # --- Open rasters ---
    src_population = rasterio.open(population_path)
    src_masks = [rasterio.open(m["path"]) for m in masks]

    try:
        _validate_rasters(src_population, src_masks)

        population_nodata = src_population.nodata if src_population.nodata is not None else -9999

        # --- Process each region ---
        for _, region in regions.iterrows():
            region_id = region[region_id_att]
            geometry = [mapping(region.geometry)]

            # Clip rasters to region extent
            try:
                pop_clipped, mask_clipped = _clip_rasters(
                    src_population, src_masks, masks, geometry,
                    population_band, population_nodata
                )
            except SkipRegion:
                continue
            except Exception as e:
                print(f"[{region_id}] Clipping failed: {e}")
                continue

            # --- Handle each mask configuration ---
            for conf in configurations:
                combined_mask = _build_combined_mask(conf, masks, mask_clipped)

                pop = pop_clipped if combined_mask is None else pop_clipped[combined_mask]
                pop = pop[pop != population_nodata]

                row = {region_id_att: region_id}
                row["value"] = pop.sum() if pop.size > 0 else value_when_no_population
                for i, m in enumerate(masks):
                    row[m["dim_name"]] = conf[i]
                out.append(row)

    finally:
        src_population.close()
        for sm in src_masks:
            sm.close()

    return pd.DataFrame(out)


# ── Helpers ────────────────────────────────────────────────────────────────────

class SkipRegion(Exception):
    """Raised when a region has no valid data and should be silently skipped."""


def _validate_rasters(src_population, src_masks: list) -> None:
    """Check that all mask rasters are compatible with the population raster."""
    for sm in src_masks:
        if sm.crs != src_population.crs:
            raise ValueError(f"CRS mismatch: population={src_population.crs}, mask={sm.crs}")
        if sm.transform != src_population.transform:
            raise ValueError(f"Transform mismatch: population={src_population.transform}, mask={sm.transform}")
        if sm.res != src_population.res:
            raise ValueError(f"Resolution mismatch: population={src_population.res}, mask={sm.res}")


def _clip_rasters(src_population, src_masks, masks, geometry, population_band, population_nodata):
    """Clip population and mask rasters to a region geometry."""
    try:
        pop_clipped = mask(src_population, geometry, crop=True, filled=True, nodata=population_nodata)[0]
        mask_clipped = [
            mask(sm, geometry, crop=True, filled=True)[0][m["band"] - 1]
            for sm, m in zip(src_masks, masks)
        ]
    except ValueError:
        raise SkipRegion()

    return pop_clipped[population_band - 1], mask_clipped


def _build_combined_mask(conf, masks, mask_clipped):
    """Combine individual mask functions into a single boolean mask."""
    combined = None
    for i, (key, mask_data) in enumerate(zip(conf, masks)):
        mf = mask_data["fun"].get(key)
        if mf is None:
            continue
        m = mf(mask_clipped[i])
        if m is None:
            continue
        combined = m if combined is None else combined & m
    return combined





def zonal_sum_by_class(
    values_path: str,
    classes_path: str, classes: Dict[str, tuple],
    zonal_path: str, id_att:str="id",
    zonal_filter = None,
    values_band:int = 0,
    classes_band:int = 0,
    clean_zonal_attributes:bool = False,
) -> gpd.GeoDataFrame:

    """
    Calculate the sum from values_path raster corresponding to classes define in the classes dictionnary on classes_path raster 
    for each polygon from the zonal_path vector file
   
    classes_path : path to raster file from which define classes
    values_path : path to raster file which contain values to sum
    zonal_path : path to polygonal vector file
    zonal_filter : a function to filter the zones and exclude some of them. The function returns True to keep, False to exclude.
    classes : dictionnary that define classes 
        This dictionnary 
            keys are the name of the output field
            values are tuples with the min and max of each classe
    clean_zonal_attributes: Set to True if you need to remove all useless attributes of the input GPKG. Then keep only the id and geometry

    Example : 

    RASTER_CLASSES_PATH = "C://mydata//raster_classes.tif"
    RASTER_VALUES_PATH = "C://mydata//raster_value.tif"
    ZONAL_FILE ="C://mydata//zonal_geopackage.gpkg"
    DICT_CLASSES = {
        "pop_tot":(0,350000), # for the total class indicate the max values
        "pop_under_500m": (0, 500),
        "pop_under_5000m": (0, 5000),
        # Add class as you need
    }   
    result_gdf=zonal_sum_by_class(RASTER_CLASSES_PATH,RASTER_VALUES_PATH,ZONAL_FILE,DICT_CLASSES)
    """
    # Load zones
    zonal = gpd.read_file(zonal_path)
    if clean_zonal_attributes: zonal = zonal[[id_att, 'geometry']]
    if zonal_filter: zonal = zonal[zonal.apply(zonal_filter, axis=1)]

    # Open raster files
    with rasterio.open(classes_path) as src_classes, rasterio.open(values_path) as src_values:

        # Test if rasters are compatible
        # TODO test also same resolution ?
        if src_classes.crs != src_values.crs:    
            print("Error: Classes and values rasters have different CRSs")
            print(src_classes.crs)
            print(src_values.crs)
        if src_classes.transform != src_values.transform:    
            print("Error: Classes and values rasters have different Transform")
            print(src_classes.transform)
            print(src_values.transform)

        # Manage NoData for values
        values_nodata = src_values.nodata if src_values.nodata is not None else -9999 

        # Process for each polygon in zonal
        for index, row in zonal.iterrows():

            # Clip raster by the polygon's geometry
            geometry = [mapping(row.geometry)]

            # Clip values rasters
            try:
                values_clipped, _ = mask(src_values, geometry, crop=True, filled=True)
                classes_clipped, _ = mask(src_classes, geometry, crop=True, filled=True)
            except:
                #print("Failed clipping", row[id_att])
                continue

            # keep band
            values_clipped = values_clipped[values_band]
            classes_clipped = classes_clipped[classes_band]

            # Ensure that the two clipped rasters have the same size
            #if values_clipped.shape != classes_clipped.shape:
            #    if verbose: print(f"Warning: the clipped raster for the polygon {index} don't have the same size")
            #    continue

            # Calculate the sum for each class
            for class_name, (min_val, max_val) in classes.items():
                # Create a boolean mask based on the condition
                class_mask = (classes_clipped >= min_val) & (classes_clipped < max_val)

                # Apply the class_mask to the values array
                # only consider the values where the class_mask is True
                values_in_class = values_clipped[class_mask]

                # Filter NoData values 
                valid_values = values_in_class[values_in_class != values_nodata]

                # Agregation : compute the sum 
                zonal.loc[index, class_name] = valid_values.sum() if valid_values.size > 0 else None

    return zonal
