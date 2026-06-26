import rasterio
import geopandas as gpd
import pandas as pd
from rasterio.mask import mask
from shapely.geometry import mapping
from typing import Dict
from math import isnan


def grid2stat(
    population_path: str,
    population_band:int = 1,
    region_path: str = None,
    region_id_att:str="id",
    region_filter = None,
    mask_path1: str = None,
    mask_fun1 = None,
    mask_band1:int = 1,
    mask_path2: str = None,
    mask_fun2 = None,
    mask_band2:int = 1,
) -> pd.DataFrame:

    # load regions, if not specified
    regions = gpd.read_file(region_path)
    if region_filter: regions = regions[regions.apply(region_filter, axis=1)]
    regions = regions[[region_id_att, 'geometry']]
    #print(len(regions))

    # output data
    out = []

    # Open raster files
    src_population = rasterio.open(population_path)
    src_mask = []
    if mask_path1: src_mask.append(rasterio.open(mask_path1))
    if mask_path2: src_mask.append(rasterio.open(mask_path2))

    #
    mask_band = [ mask_band1, mask_band2 ]

    try:

        '''
        # show information on bands and band names
        for dataset in [src_population, src_mask]:
            print(dataset)
            # Get all band names as a tuple
            band_names = dataset.descriptions
            print("Band names:", band_names)
            # Pair each 1-based band index with its name
            for idx, name in zip(dataset.indexes, dataset.descriptions):
                print(f"Band {idx}: {name}")
        '''

        # Test if mask rasters are compatible with population raster
        for sm in src_mask:
            if sm.crs != src_population.crs:    
                print("Error: Rasters have different CRSs")
                print(sm.crs)
                print(src_population.crs)
            if sm.transform != src_population.transform:    
                print("Error: Rasters have different Transform")
                print(sm.transform)
                print(src_population.transform)
            if sm.res[0] != src_population.res[0] or sm.res[1] != src_population.res[1]:
                print("Error: Rasters have different resolutions")
                print(sm.res)
                print(src_population.res)

        # Manage NoData
        population_nodata = src_population.nodata if src_population.nodata is not None else -9999 
        #mask_nodata = src_mask.nodata if src_mask.nodata is not None else -9999 

        # Process each region
        for _, region in regions.iterrows():

            # Clip rasters by region geometry
            geometry = [mapping(region.geometry)]
            try:
                # clip population
                population_clipped, _ = mask(src_population, geometry, crop=True, filled=True, nodata=population_nodata)

                # clip masks
                mask_clipped = []
                for sm in src_mask:
                    mc, _ = mask(sm, geometry, crop=True, filled=True)
                    mask_clipped.append(mc)
            except Exception as e:
                if type(e).__name__ == "ValueError": continue
                print(f"Failed clipping {region[region_id_att]}: {e}")
                continue

            # keep usefull bands TODO do that earlier? before clipping ? at src level ?
            population_clipped = population_clipped[population_band-1]
            mask_clipped = [ mc[band-1] for mc, band in zip(mask_clipped, mask_band) ]

            # Ensure that the two clipped rasters have the same size
            #if values_clipped.shape != classes_clipped.shape:
            #    if verbose: print(f"Warning: the clipped raster for the polygon {index} don't have the same size")
            #    continue

            # TODO currently only a single mask. make it possible to have several ?
            for indic1, classes1 in mask_fun1.items():
                for indic2, classes2 in mask_fun2.items():
                    for class_name1, mf1 in classes1.items():
                        for class_name2, mf2 in classes2.items():

                            # Create a boolean mask based on the mask function
                            m1 = mf1(mask_clipped[0])
                            m2 = mf2(mask_clipped[1])

                            # and apply mask to the pop array: only keep pop values where the mask is True
                            p = population_clipped
                            if m1: p = p[m1]
                            if m2: p = p[m2]

                            # Filter NoData values 
                            p = p[p != population_nodata]

                            #if pop.size == 0: continue

                            # Agregation : compute the sum and make data item
                            ob = { "value" : p.sum() if p.size > 0 else None }
                            ob[region_id_att] = region[region_id_att]
                            if class_name1: ob[indic1] = class_name1
                            if class_name2: ob[indic2] = class_name2
                            out.append(ob)
    finally:
        # close population file
        src_population.close()
        # close mask files
        for sm in src_mask: sm.close()

    return pd.DataFrame(out)









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
