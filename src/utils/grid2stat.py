import rasterio
import geopandas as gpd
import pandas as pd
from rasterio.mask import mask
from shapely.geometry import mapping
from typing import Dict
from math import isnan




def grid2stat(
    population_path: str,
    population_band:int = 0,
    region_path: str = None, region_id_att:str="id",
    region_filter = None,
    mask_path: str = None,
    mask_fun = None,
    mask_band:int = 0,
    verbose:bool = True,
) -> pd.DataFrame:

    # load regions, if not specified
    regions = gpd.read_file(region_path)
    if region_filter: regions = regions[regions.apply(region_filter, axis=1)]
    regions = regions[[region_id_att, 'geometry']]
    print(len(regions))

    # output data
    out = []

    # Open raster files
    with rasterio.open(mask_path) as src_mask, rasterio.open(population_path) as src_population:

        for dataset in [src_population, src_mask]:
            print(dataset)
            # Get all band names as a tuple
            band_names = dataset.descriptions
            print("Band names:", band_names)
            # Pair each 1-based band index with its name
            for idx, name in zip(dataset.indexes, dataset.descriptions):
                print(f"Band {idx}: {name}")

        # Test if rasters are compatible
        if src_mask.crs != src_population.crs:    
            print("Error: Rasters have different CRSs")
            print(src_mask.crs)
            print(src_population.crs)
        if src_mask.transform != src_population.transform:    
            print("Error: Rasters have different Transform")
            print(src_mask.transform)
            print(src_population.transform)
        if src_mask.res[0] != src_population.res[0] or src_mask.res[1] != src_population.res[1]:
            print("Error: Rasters have different resolutions")
            print(src_mask.res)
            print(src_population.res)


        # Manage NoData for values
        values_nodata = src_population.nodata if src_population.nodata is not None else -9999 

        # Process each region
        for _, region in regions.iterrows():

            # Clip rasters by region geometry
            geometry = [mapping(region.geometry)]
            try:
                population_clipped, _ = mask(src_population, geometry, crop=True, filled=True)
                mask_clipped, _ = mask(src_mask, geometry, crop=True, filled=True)
            except:
                #print("Failed clipping", row[id_att])
                continue

            # keep band
            #TODO do before clipping ? at src level ?
            population_clipped = population_clipped[population_band]
            mask_clipped = mask_clipped[mask_band]

            # Ensure that the two clipped rasters have the same size
            #if values_clipped.shape != classes_clipped.shape:
            #    if verbose: print(f"Warning: the clipped raster for the polygon {index} don't have the same size")
            #    continue

            # TODO currently only a single mask. make it possible to have several.
            for indic, classes in mask_fun.items():

                for class_name, mf in classes.items():

                    # Create a boolean mask based on the condition
                    class_mask = mf(mask_clipped)

                    # Apply the class_mask to the values array
                    # only consider the values where the class_mask is True
                    values_in_class = population_clipped[class_mask]

                    # Filter NoData values 
                    valid_values = values_in_class[values_in_class != values_nodata]

                    if valid_values.size == 0: continue

                    # Agregation : compute the sum and make data item
                    ob = { "value" : valid_values.sum() }
                    ob[region_id_att] = region[region_id_att]
                    ob[indic] = class_name
                    out.append(ob)

    return pd.DataFrame(out)






def zonal_sum_by_class(
    values_path: str,
    classes_path: str, classes: Dict[str, tuple],
    zonal_path: str, id_att:str="id",
    zonal_filter = None,
    verbose:bool = True,
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
