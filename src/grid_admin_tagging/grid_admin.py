# Take some gridded dataset and assigne to it some administrative unit code (i.e. nuts or country code)

import pandas as pd
import fiona
from rtree import index
from shapely.geometry import shape, Point
from datetime import datetime #TODO check that

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.gridutils import get_cell_id



def produce_correspondance_table(
    admin_units_dataset, #GPKG - prepared. polygons with id
    admin_code_attribute,
    resolution,
    output_table_path,
    tolerance_distance = None,
):

    print(datetime.now(), "Spatial index patches")

    crs = None
    xmin,ymin,xmax,ymax = None
    # spatial index items
    items = []
    with fiona.open(admin_units_dataset) as src:
        # get CRS and bounds
        crs = src.crs
        (xmin,ymin,xmax,ymax) = src.bounds

        i=0
        for patch in src:
            g = shape(patch["geometry"])
            items.append((i, g.bounds, None))
            i+=1

    # build index
    idx = index.Index(((i, box, obj) for i, box, obj in items))
    del items


    # prepare output data structure
    data = { 'GRD_ID':[], 'ID': [] }

    # go through cells using bounds
    r2 = resolution/2
    d = r2* 1.4142 + tolerance_distance
    for x in range(xmin, xmax+1, resolution):
        for y in range(ymin, ymax+1, resolution):

            # add entry for grid cell
            cid = get_cell_id(crs=crs, res_m=resolution, x=x, y=y)
            data['GRD_ID'].append(cid)

            # get cell center coordinates
            xc = x+r2, yc = y+r2

            # get matches nearby
            query_envelope = (xc-d, yc-d, xc+d, yc+d)
            candidate_ids = list(idx.intersection(query_envelope))

            # set of admin codes
            ccs = set()

            # check distance
            query_point = Point(xc, yc)
            for fid in candidate_ids:
                feature = src[fid]
                geom = shape(feature["geometry"])
                if query_point.distance(geom) > d: continue

                cc = feature['properties'][admin_code_attribute]
                ccs.add(str(cc))

            # store list of ids
            set = ",".join(sorted(set))
            data['ID'].append(set)

    # save output
    print(datetime.now(), "save as parquet")
    out = pd.DataFrame(data)
    out.to_parquet(output_table_path)

