import sys
import os
import csv
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.gridutils import grid_to_geopackage

# location of the country files
input_path = "/home/juju/geodata/census/2021/input20250123/"

# location of the output files (geopackage, csv, parquet)
output_path = "/home/juju/gisco/census_2021_production/"
CONFIDENTIAL_VALUE = -8888
NA_VALUE = -9999


'''
DATAFLOW,FREQ,
STAT,
SPATIAL,TIME_PERIOD,
OBS_VALUE,
NOT_COUNTED_PROPORTION,GENERAL_STATUS,
OBS_STATUS,STATUS,
LAND_SURFACE,
SPECIAL_VALUE,APPROXIMATELY_LOCATED_POPULATION_PROPORTION,OBS_NOTE,MEASURE,
MEASUREMENT_METHOD,UNIT_MEASURE,
CONVENTIONALLY_LOCATED_PROPORTION,UNIVERSE,POPULATED,
AREA_OF_DISSEMINATION,INSPIREID

ESTAT:DF_CENSUS_GRID_2021(2.0),A10,
T,
LU_CRS3035RES1000mN2975000E4014000,2021,
0,
0,final,
,final,
0,
,0,,
populationAtResidencePlace,count,
PS,0,,0,
LU,


ESTAT:DF_CENSUS_GRID_2021(2.0),A10,
CHG_IN,
LU_CRS3035RES1000mN2977000E4014000,2021,
,
0,final,
,final,
0.0935,
confidential,0,,
populationAtResidencePlace,count,
PS,0,,1,
LU,


stat indic: STAT
grid cell: SPATIAL
value: OBS_VALUE
confidential: SPECIAL_VALUE
'''


# output cells, as a dictionnary indexed by cell_id
cells = {}

#for cc in ["AT","PT", "BE", "LU"]:
for cc in ["AT","BE","BG","CH","CY","CZ","DE","DK","EE","EL","ES","FI","FR","HR","HU","IE","IT","LI","LT","LU","LV","MT","NL","NO","PL","PT","RO","SE","SI","SK"]:

    print(datetime.now(), cc)

    # parse country file
    with open(input_path + "CENSUS_GRID_N_" + cc + "_2021.csv") as f:
        rows = list(csv.DictReader(f))
        for row in rows:

            # get cell id (get rid of country code prefix, except for unallocated data)
            id = row["SPATIAL"][3:]
            if id == "unallocated": id = row["SPATIAL"]

            # get cell, create one if it does not exist yet
            cell = cells.get(id)
            if cell is None:
                cell = { "GRD_ID": id, "CNTR_ID": [cc], "POPULATED": 0 }
                cells[id] = cell

            # country code
            cnt = cell["CNTR_ID"]
            if cc not in cnt: cnt.append(cc)

            # extract row base data
            stat = row["STAT"]
            if stat == "Y15-64": stat = "Y_1564"
            stat_ci = row["SPECIAL_VALUE"]
            value = row["OBS_VALUE"]

            # populated
            # as soon as a populated value is 1 or an OBS_VALUE > 0 or confidential is found for a cell, we consider it as populated, even if the POPULATED column value is missing or 0.
            # do that, to force compliance with specs
            if cell.get("POPULATED") == "1" or (value != "" and int(value) > 0) or stat_ci == "confidential": cell["POPULATED"] = 1

            # land surface
            # the value is repeated for all stat positions: use only the one for stat "T"
            if stat == "T":
                v = row["LAND_SURFACE"]
                if v is not None and v != "":
                    v = float(v)
                    if cell.get("LAND_SURFACE") is None:
                        cell["LAND_SURFACE"] = v
                    else:
                        cell["LAND_SURFACE"] += v

            # NA case
            if value is None or value == "":
                cell[stat] = NA_VALUE
                continue

            # allow (or not ?) dissemination of values that are provided but declared as confidential
            # TODO decide !
            stat_ci = ""

            # get previous cell value for that stat
            prv_value = cell.get(stat)
            # if previous cell value is confidential or NA, keep it as it is, even if new value is available and not confidential.
            # it could happen when 2 countries report data on the same cell and one of them reports confidential values or NA values.
            if prv_value == CONFIDENTIAL_VALUE or prv_value == NA_VALUE: continue

            # if new cell value confidential, set cell value to confidential
            if stat_ci == "confidential":
                cell[stat] = CONFIDENTIAL_VALUE
            # new cell value not confidential: keep or add value
            elif stat_ci == "" or stat_ci == "notApplicable":
                if prv_value is None:
                    cell[stat] = int(value)
                else:
                    cell[stat] += int(value)
            else:
                print("unexpected confidential value found: " + stat_ci, cc, value)


print(datetime.now(), "post process cells. Nb cells =", len(cells))

# extract cells from dictionnary
cells = list(cells.values())

properties = ['GRD_ID', 'T', 'M', 'F', 'Y_LT15', 'Y_1564', 'Y_GE65', 'EMP', 'NAT', 'EU_OTH', 'OTH', 'SAME', 'CHG_IN', 'CHG_OUT', 'LAND_SURFACE', 'POPULATED', 'CNTR_ID']
cells_ = []
for cell in cells:

    # check all values are provided. Otherwise, set to 'not available'
    t = cell.get("T")
    for stat in properties:
        if stat not in cell:
            cell[stat] = 0 if t==0 else NA_VALUE

    # sort country codes in cell
    cell["CNTR_ID"] = "-".join(sorted(cell["CNTR_ID"]))

    # round land surface to 4 decimals
    #cell["LAND_SURFACE"] = round(cell["LAND_SURFACE"], 6)
    # force below 1
    if cell["LAND_SURFACE"] >1: cell["LAND_SURFACE"] = 1

    # sort cell properties
    cell = { k: cell[k] for k in properties if k in cell }

    # store new ordered cells
    cells_.append(cell)

# keep new list of cells with ordered properties
cells = cells_

print(datetime.now(), "store as geopackage")
grid_to_geopackage(cells, output_path + "census_grid_2021.gpkg", grid_resolution=1000, ignore_errors=True, layer_name="census_grid_2021")

print(datetime.now(), "store as csv")
with open(output_path + "census_grid_2021.csv", "w") as f:
    writer = csv.DictWriter(f, fieldnames=cells[0].keys())
    writer.writeheader()
    writer.writerows(cells)

print(datetime.now(), "store as parquet")
pq.write_table(pa.Table.from_pylist(cells), output_path + "census_grid_2021.parquet")

#TODO store as geotiff


