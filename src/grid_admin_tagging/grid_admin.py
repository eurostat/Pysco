# Take some gridded dataset and assigne to it some administrative unit code (i.e. nuts or country code)

import pandas as pd
import fiona
from rtree import index
from shapely.geometry import shape, Point
from datetime import datetime

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))



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

    #
    crs = str(crs).replace("EPSG:", "").replace("epsg:", "")

    # prepare output data structure
    data = { 'GRD_ID':[], 'ID': [] }
    r2 = resolution/2
    d = r2* 1.4142 + tolerance_distance

    for x in range(xmin, xmax+1, resolution):

        print(datetime.now(), x)

        for y in range(ymin, ymax+1, resolution):

            # get matches nearby
            xc = x+r2; yc = y+r2
            envelope = (xc-d, yc-d, xc+d, yc+d)
            candidate_ids = idx.intersection(envelope)
            if not candidate_ids: continue

            # set of admin codes
            codes = set()

            candidate_ids = list(candidate_ids)

            # check distance
            query_point = Point(xc, yc)
            for fid in candidate_ids:
                f = features[fid]
                #TODO check if this is really necessary
                if query_point.distance(f["g"]) > d: continue
                cc = f['properties'][admin_code_attribute]
                codes.add(str(cc))

            #
            if len(codes)==0: continue

            # add entry for grid cell
            data['GRD_ID'].append(
                'CRS' + crs + 'RES' + str(resolution) + 'mN' + str(int(y)) + 'E' + str(int(x))
            )

            # store list of admin ids
            codes = "-".join(sorted(codes))
            data['ID'].append(codes)



    # save output
    print(datetime.now(), "save as parquet")
    out = pd.DataFrame(data)
    out.to_parquet(output_table_path)





produce_correspondance_table(
    "/home/juju/geodata/gisco/admin_tagging/final.gpkg",
    #"/home/juju/geodata/gisco/CNTR_RG_01M_2024_3035.gpkg",
    "CNTR_ID",
    100,
    "/home/juju/Bureau/output.parquet",
    tolerance_distance = 500,
    num_processors_to_use=1,
    bbox = (4030000, 2930000, 4060000, 2960000)
    #bbox = ( 1000000, 500000, 6000000, 5500000 )
)

# to csv
print("to csv")
pd.read_parquet("/home/juju/Bureau/output.parquet").to_csv("/home/juju/Bureau/output.csv", index=False)

