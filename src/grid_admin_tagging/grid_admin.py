# Take some gridded dataset and assigne to it some administrative unit code (i.e. nuts or country code)

import fiona


def produce_correspondance_table(
    admin_units_dataset, #GPKG - prepared. polygons with id
    admin_code_attribute,
    resolution,
    output_table_path,
    tolerance_distance = None,
):
    pass

    #print(datetime.now(), gpkg)

    crs = None
    xmin,ymin,xmax,ymax = None
    with fiona.open(admin_units_dataset) as src:
        # get CRS and bounds
        crs = src.crs
        (xmin,ymin,xmax,ymax) = src.bounds

    # build adm patches spatial index

    #go through cells using bounds

    #make output dataframe

    #for each cell
        #get cell center coordinates
        #get admin patches using spatial index with distance smaller than resolution/sqrt(2) OR tolerance_distance
        #get list of ids of them
        #make cell_id
        #add row cell_id, list

    #store output dataframe

