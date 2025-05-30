# Take some gridded dataset and assigne to it some administrative unit code (i.e. nuts or country code)

import pandas as pd
import fiona
from rtree import index
from datetime import datetime #TODO check that


def produce_correspondance_table(
    admin_units_dataset, #GPKG - prepared. polygons with id
    admin_code_attribute,
    resolution,
    output_table_path,
    tolerance_distance = None,
):
    pass

    print(datetime.now(), "Spatial index patches")

    crs = None
    xmin,ymin,xmax,ymax = None
    # spatial index items
    items = []
    codes = []
    with fiona.open(admin_units_dataset) as src:
        # get CRS and bounds
        crs = src.crs
        (xmin,ymin,xmax,ymax) = src.bounds

        i=0
        for _, patch in src.items():
            #TODO
            items.append((i, (x,y,x,y), None))
            codes.append(patch['properties'][admin_code_attribute])
            i+=1

    # build index
    idx = index.Index(((i, box, obj) for i, box, obj in items))
    del items


    # prepare output data structure
    data = { 'GRD_ID':[], 'ID': [] }

    #go through cells using bounds
    r2 = resolution/2
    for x in range(xmin, xmax+1, resolution):
        for y in range(ymin, ymax+1, resolution):
            pass

            #get cell center coordinates
            xc = x+r2, yc = y+r2

            #TODO
            #get admin patches using spatial index with distance smaller than resolution/sqrt(2) OR tolerance_distance
            #get list of ids of them
            #make cell_id
            #add row cell_id, list

    # save output
    print(datetime.now(), "save as parquet")
    out = pd.DataFrame(data)
    out.to_parquet(output_table_path)

