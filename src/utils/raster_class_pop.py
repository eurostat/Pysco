import rasterio
import geopandas as gpd
import numpy as np
from rasterio.mask import mask
from shapely.geometry import mapping
from typing import Dict
from datetime import datetime

def zonal_sum_by_class(
    classes_path: str, values_path: str, zonal_path: str, classes: Dict[str, tuple]
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
    zonal=gpd.read_file(zonal_path)
    
    # Create a column for each class
    for class_name in classes.keys():
         zonal[class_name]=np.nan

    # Open raster files
    with rasterio.open(classes_path) as src_classes, rasterio.open(values_path) as src_values:
        # Test if CRS and transformation are compatible
        if src_classes.crs != src_values.crs or src_classes.transform != src_values.transform:    
            print("Warning: Classes and values rasters have different metadata (CR/Transform)")
            # For simplify, we suppose that the rasters files are aligned
            # TODO : step for reproject and resample if it's necessary 
            
        # Read data
        classes_array = src_classes.read(1)
        values_array = src_values.read(1)
        
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
                values_clipped = values_clipped[0] # Prendre le premier (et unique) band
                
                # Clip classes raster
                classes_clipped, classes_transform = mask(src_classes, geometry, crop=True, filled=True)
                classes_clipped = classes_clipped[0] # Prendre le premier (et unique) band
                
                # Ensure that the two clipped raster have the same size
                if values_clipped.shape != classes_clipped.shape:
                    print(f"Warning: the clipped raster for the polygon {index} don't have the same size")
                    # TODO : Manage the resampling 
                    continue
            except Exception as e:
                print(f"Error during the clipping of polygon {index}: {e}")
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
                if valid_values.size > 0:
                    total_sum = valid_values.sum()
                    zonal.loc[index, class_name] = total_sum
                else:
                    zonal.loc[index, class_name] = 0.0 # 0 si no pixels match the conditions 

    return zonal


def zonal_sum_by_class_to_gpkg(
    # acc_path: str, pop_path: str, zones_path: str, classes: Dict[str, tuple]
    classes_path: str, values_path: str, zonal_path: str, classes: Dict[str, tuple],export_file : str,layer:str
) -> bool:
     """
    Compute the zonal_sum_by_class function and save the result in a GeoPackage file
   
    classes_path : path to raster file from which define classes
    values_path : path to raster file which contain values to sum
    zonal_path : path to polygonal vector file
    classes : dictionnary that define classes 
        This dictionnary 
            keys are the name of the output field
            values are tuples with the min and max of each classe
    export_file : path to the exported file
    layer : Name of result layer in the Geopackage


    Example : 
    
    RASTER_CLASSES_PATH = "C://mydata//raster_classes.tif"
    RASTER_VALUES_PATH = "C://mydata//raster_value.tif"
    ZONAL_FILE ="C://mydata//zonal_geopackage.gpkg"
    EXPORT_FILE="C://mydata//result.gpkg" 
    EXPORT_LAYER="mylayer"
    DICT_CLASSES = {
        "pop_tot":(0,350000), # for the total class indicate the max values
        "pop_under_500m": (0, 500),
        "pop_under_5000m": (0, 5000),
        # Add class as you need
    }   
    result_gdf=zonal_sum_by_class(RASTER_CLASSES_PATH,RASTER_VALUES_PATH,ZONAL_FILE,DICT_CLASSES,EXPORT_FILE,EXPORT_LAYER)
    """

    try:
        zonal_result = zonal_sum_by_class(
        classes_path, values_path, zonal_path, classes
        )
        zonal_result.to_file(export_file,driver='GPKG', layer=layer)
    except Exception as e:
         print(f"Error during processing : {e}")
         return False
    return True


def multiple_zonal_sum_by_class_to_gpkg(
    # acc_path: str, pop_path: str, zones_path: str, classes: Dict[str, tuple]
    #classes_path: str, values_path: str, zonal_path: str, classes: Dict[str, tuple],export_file : str,layer:str
    classes_paths: list, values_path: str, zonal_path: str, classes: Dict[str, tuple]
) -> bool:
     """
    Compute the multiple zonal_sum_by_class function and save the result in GeoPackage files based on differents classes raster but with the same values raster, zonal geopackage
    and classes dictionary 
   
    classes_paths : an list of list structured as  [classes_path, export_file, layer]
    values_path : path to raster file which contain values to sum
    zonal_path : path to polygonal vector file
    classes : dictionnary that define classes 
        This dictionnary 
            keys are the name of the output field
            values are tuples with the min and max of each classe

    Example : 

    RASTER_CLASSES_PATHS=[
                ["C://mydata//raster_classes1.tif","C://mydata//result1.gpkg","myLayer" ],
                ["C://mydata//raster_classes2.tif","C://mydata//result2.gpkg","myLayer" ]
    ]
    RASTER_VALUES_PATH = "C://mydata//raster_value.tif"
    ZONAL_FILE ="C://mydata//zonal_geopackage.gpkg"
    DICT_CLASSES = {
        "pop_tot":(0,350000), # for the total class indicate the max values
        "pop_under_500m": (0, 500),
        "pop_under_5000m": (0, 5000),
        # Add class as you need
    }   
    result=multiple_zonal_sum_by_class_to_gpkg(RASTER_CLASSES_PATHS,RASTER_VALUES_PATH, ZONAL_FILE,DICT_CLASSES)
    """
    try:
        for p in classes_paths:
            print("{} - Start file : {}".format(datetime.now(),p[0]))
            result = zonal_sum_by_class_to_gpkg(p[0], values_path, zonal_path, classes,p[1],p[2])
            print("{} - end file : {}".format(datetime.now(),p[0]))

    except Exception as e:
        print("End with Exception")
        return False
    print("End Successfully")
    return True


