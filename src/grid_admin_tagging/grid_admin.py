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
    bbox = None,
    tolerance_distance = None,
):

    print(datetime.now(), "Load admin patches")

    # spatial index items, get CRS, get bbox
    crs = None
    idx = []
    features = []
    with fiona.open(admin_units_dataset, 'r') as src:
        # get CRS and bounds
        crs = src.crs
        if bbox == None:
            bbox = src.bounds

        i=0
        for f in src.items(bbox=bbox):
            f = f[1]
            g = shape(f["geometry"])
            idx.append((i, g.bounds, None))
            f["g"] = g
            features.append(f)
            i+=1

    # build index
    idx = index.Index(((i, box, obj) for i, box, obj in idx))

    # bbox
    (xmin,ymin,xmax,ymax) = bbox

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
            xc = x+r2
            yc = y+r2

            # get matches nearby
            query_envelope = (xc-d, yc-d, xc+d, yc+d)
            candidate_ids = list(idx.intersection(query_envelope))

            # set of admin codes
            codes = set()

            # check distance
            query_point = Point(xc, yc)
            for fid in candidate_ids:
                f = features[fid]
                g = f["g"]
                if query_point.distance(g) > d: continue

                cc = f['properties'][admin_code_attribute]
                codes.add(str(cc))

            # store list of ids
            codes = ",".join(sorted(codes))
            print(codes)
            data['ID'].append(codes)

    # save output
    print(datetime.now(), "save as parquet")
    out = pd.DataFrame(data)
    out.to_parquet(output_table_path)




produce_correspondance_table(
    "/home/juju/geodata/gisco/CNTR_RG_01M_2024_3035.gpkg",
    "CNTR_ID",
    1000,
    "/home/juju/Bureau/output.parquet",
    tolerance_distance = 200,
    bbox = (4030000, 2930000, 4060000, 2960000)
)
