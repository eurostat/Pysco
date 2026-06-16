import rasterio
import geopandas as gpd
from rasterio.mask import mask
from shapely.geometry import mapping
from typing import Dict
from math import isnan


def zonal_sum_by_class(
    classes_path: str, values_path: str, zonal_path: str, classes: Dict[str, tuple],
    gpkg_path:str=None, gpkg_layer:str=None,
    csv_path:str=None, id_att:str="id",
    verbose:bool = True,
    class_name_change_fun = None,
    rounding_fun = None,
    values_band:int = 0,
    classes_band:int = 0,
) -> gpd.GeoDataFrame:

    """
    Calculate the sum from values_path raster corresponding to classes define in the classes dictionnary on classes_path raster 
    for each polygon from the zonal_path vector file
   
    classes_path : path to raster file from which define classes
    values_path : path to raster file which contain values to sum
    zonal_path : path to polygonal vector file
    classes : dictionnary that define classes 
        This dictionnary 
            keys are the name of the output field
            values are tuples with the min and max of each classe
    class_name_change_fun : a function str->str to change the class names on the fly. may be usefull to add a suffix with a year for example.
    rounding_fun: a function number->number to apply to the final numbers, to round them for example.

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
    # Load vector file
    zonal = gpd.read_file(zonal_path)
    #TODO apply filter here

    # Create a column for each class
    #for class_name in classes.keys(): zonal[class_name]=None

    # Open raster files
    with rasterio.open(classes_path) as src_classes, rasterio.open(values_path) as src_values:
        # Test if CRS and transformation are compatible
        if src_classes.crs != src_values.crs:    
            print("Error: Classes and values rasters have different CRSs")
            print(src_classes.crs)
            print(src_values.crs)
        if src_classes.transform != src_values.transform:    
            print("Error: Classes and values rasters have different Transform")
            print(src_classes.transform)
            print(src_values.transform)
            # For simplify, we suppose that the rasters files are aligned
            # TODO : step for reproject and resample if it's necessary 

        # Manage NoData for values
        values_nodata = src_values.nodata if src_values.nodata is not None else -9999 

        # Process for each polygon in zonal
        for index, row in zonal.iterrows():
            # Clip raster by the polygon's geometry
            geometry = [mapping(row.geometry)]
            try:
                # Découpage du raster POP et de sa fenêtre
                # Clip values raster
                values_clipped, values_transform = mask(src_values, geometry, crop=True, filled=True)
                values_clipped = values_clipped[values_band]

                # Clip classes raster
                classes_clipped, classes_transform = mask(src_classes, geometry, crop=True, filled=True)
                classes_clipped = classes_clipped[classes_band]

                # Ensure that the two clipped raster have the same size
                if values_clipped.shape != classes_clipped.shape:
                    if verbose: print(f"Warning: the clipped raster for the polygon {index} don't have the same size")
                    # TODO : Manage the resampling 
                    continue
            except Exception as e:
                if verbose: print(f"Problem during the clipping of polygon {index}: {e}")
                continue

            # Calculate the sum for each classes
            for class_name, (min_val, max_val) in classes.items():
                # Create a boolean mask based on the condition
                class_mask = (classes_clipped >= min_val) & (classes_clipped <= max_val)

                # Apply the class_mask to the values array
                # only consider the values where the class_mask is True
                values_in_class = values_clipped[class_mask]

                # Filter NoData values 
                valid_values = values_in_class[values_in_class != values_nodata]

                # Agregation : compute the sum 
                if class_name_change_fun is not None: class_name = class_name_change_fun(class_name)
                zonal.loc[index, class_name] = valid_values.sum() if valid_values.size > 0 else None

    # column names
    cols = list(classes.keys())
    if class_name_change_fun is not None: cols = [class_name_change_fun(x) for x in cols]

    # apply rounding function
    if rounding_fun is not None:
        zonal[cols] = zonal[cols].apply(lambda s: s.map(lambda v: None if v is None or isnan(v) else rounding_fun(v)))

    # export to GPKG
    if gpkg_path is not None:
        zonal.to_file(gpkg_path,driver='GPKG', layer=gpkg_layer)

    # export to CSV
    if csv_path is not None:
        zonal[ [id_att] + cols ].to_csv(csv_path, index=False)

    return zonal

