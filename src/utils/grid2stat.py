import rasterio
import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio.mask import mask
from shapely.geometry import mapping
from typing import Dict
from itertools import product

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.utils import weighted_median



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

    # Open rasters: population and masks
    src_population = rasterio.open(population_path)
    src_masks = [rasterio.open(m["path"]) for m in masks]

    out = []
    try:
        # Check rasters are compatible
        _validate_rasters(src_population, src_masks)

        # Set no data value for population
        population_nodata = src_population.nodata if src_population.nodata is not None else -9999

        # Process each region
        for _, region in regions.iterrows():

            # get region id and geometry
            region_id = region[region_id_att]
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
                row["value"] = pop.sum() if pop.size > 0 else value_when_no_population
                for i, m in enumerate(masks):
                    row[m["dim_name"]] = conf[i]
                out.append(row)

    finally:
        # close all files
        src_population.close()
        for sm in src_masks:
            sm.close()

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
    Compute weighted average stats on regions from raster data, one with the indicator to average, and another one with the weight (i.e. population).

    Args:
        indic_path:             Path to the indicator raster file.
        weight_path:            Path to the weight raster file.
        indic_band:             Band index (1-based) to read from the indicator raster.
        weight_band:            Band index (1-based) to read from the weights raster.
        region_path:            Path to the regions vector file.
        region_id_att:          Attribute name used as region identifier.
        region_filter:          Optional callable(row) -> bool to filter regions.
        masks:                  List of mask dicts with keys: 'path', 'band', 'fun', 'dim_name'.

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

    # Open rasters: indic, weights and masks
    src_indic = rasterio.open(indic_path)
    src_weight = rasterio.open(weight_path)
    src_masks = [rasterio.open(m["path"]) for m in masks]

    out = []
    try:
        # Check rasters are compatible
        _validate_rasters(src_indic, [src_weight] + src_masks)

        # Set no data value for population
        indic_nodata = src_indic.nodata if src_indic.nodata is not None else -9999

        # function to make a row template
        def make_row(region_id, value, type, conf):
            row = {region_id_att: region_id, "INDIC": type}
            row["value"] = value
            for i, m in enumerate(masks):
                row[m["dim_name"]] = conf[i]

        # Process each region
        for _, region in regions.iterrows():

            # get region id and geometry
            region_id = region[region_id_att]
            geometry = [mapping(region.geometry)]

            # Clip rasters to region geometry
            try:
                indic_clipped = mask(src_indic, geometry, crop=True, filled=True, nodata=indic_nodata)[0][indic_band - 1]
                weight_clipped = mask(src_weight, geometry, crop=True, filled=True)[0][weight_band - 1]
                mask_clipped = [
                    mask(sm, geometry, crop=True, filled=True)[0][m["band"] - 1]
                    for sm, m in zip(src_masks, masks)
                ]
            except SkipRegion: continue
            except Exception as e:
                print(f"[{region_id}] Clipping failed: {e}")
                continue

            # handle each mask configuration
            for conf in configurations:

                # get boolean mask
                combined_mask = _build_combined_mask(conf, masks, mask_clipped)

                # apply combined mask identically to indic and weight
                indic  = indic_clipped  if combined_mask is None else indic_clipped[combined_mask]
                weight = weight_clipped if combined_mask is None else weight_clipped[combined_mask]

                # keep only pixels where indic is valid (same boolean reused for both)
                #valid = indic != indic_nodata
                valid = ~np.isnan(indic) if np.isnan(indic_nodata) else (indic != indic_nodata) & (weight != src_weight.nodata)
                indic = indic[valid]
                weight = weight[valid]

                # compute weighted average
                wa = (indic * weight).sum() / weight.sum()

                # compute median
                wmed = weighted_median(indic, weight)

                # make data item
                row = make_row(region_id, wa, "WEIGHTED_AVERAGE", conf)
                out.append(row)
                row = make_row(region_id, wmed, "WEIGHTED_MEDIAN", conf)
                out.append(row)

    finally:
        # close all files
        src_indic.close()
        src_weight.close()
        for sm in src_masks:
            sm.close()

    return pd.DataFrame(out)






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
        pop_clipped = mask(src_population, geometry, crop=True, filled=True, nodata=population_nodata)[0][population_band - 1]
        mask_clipped = [
            mask(sm, geometry, crop=True, filled=True)[0][m["band"] - 1]
            for sm, m in zip(src_masks, masks)
        ]
    except ValueError: raise SkipRegion()

    return pop_clipped, mask_clipped


def _build_combined_mask(conf, masks, mask_clipped):
    """Combine individual mask functions into a single boolean mask."""
    combined = None
    for i, (key, mask_data) in enumerate(zip(conf, masks)):
        mf = mask_data["fun"].get(key)
        if mf is None: continue
        m = mf(mask_clipped[i])
        if m is None: continue
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
