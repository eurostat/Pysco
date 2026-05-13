import sys
import os
import csv
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.gridutils import grid_to_geopackage


input_path = "/home/juju/geodata/census/2021/input20250123/"
output_path = "/home/juju/gisco/census_2021_production/"
confidential_value = -8888
na_value = -9999


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


# output cells, as dict indexed by cell_id
cells = {}

#for cc in ["NO","PL","PT","RO","SE","SI","SK"]:
for cc in ["AT","BE","BG","CH","CY","CZ","DE","DK","EE","EL","ES","FI","FR","HR","HU","IE","IT","LI","LT","LU","LV","MT","NL","NO","PL","PT","RO","SE","SI","SK"]:

    print(datetime.now(), cc)

    with open(input_path + "CENSUS_GRID_N_" + cc + "_2021.csv") as f:
        rows = list(csv.DictReader(f))
        for row in rows:

            # get cell id
            id = row["SPATIAL"][3:]

            if id == "unallocated":
                # TODO store that somewhere. cells without geometry ? external file ?
                #print("skipping unallocated", row["STAT"], cc, row["OBS_VALUE"])
                continue

            # get cell
            cell = cells.get(id)

            # no cell: create one
            if cell is None:
                cell = { "GRD_ID": id, "CNTR_ID": [cc] }
                cells[id] = cell

            # country code
            cnt = cell["CNTR_ID"]
            if cc not in cnt: cnt.append(cc)

            # land surface
            v = row["LAND_SURFACE"]
            lsu = cell.get("LAND_SURFACE")
            if lsu is None:
                cell["LAND_SURFACE"] = v
            else:
                cell["LAND_SURFACE"] += v

            # get row info
            stat = row["STAT"]
            if stat == "Y15-64": stat = "Y_1564"
            stat_ci = row["SPECIAL_VALUE"]
            value = row["OBS_VALUE"]
            if value is None or value == "": value = 0
            value = int(value)

            # populated
            # as soon as an OBS_VALUE > 0 is found for a cell, we consider it as populated, even if the POPULATED column value is missing or 0.
            popu = cell.get("POPULATED")
            if popu is None or popu == "": popu = 0
            popu = int(popu)
            if popu > 0 or value > 0: cell["POPULATED"] = 1

            # get previous cell value for that stat
            prv_value = cell.get(stat)
            # if previous cell value is confidential, keep it confidential, even if new value is not confidential
            if prv_value == confidential_value: continue

            # if new cell value confidential, set cell value to confidential
            if stat_ci == "confidential":
                cell[stat] = confidential_value
            # new cell value not confidential
            elif stat_ci == "" or stat_ci == "notApplicable":
                if prv_value is None:
                    cell[stat] = value
                else:
                    cell[stat] += value
            else:
                print("unexpected confidential value found: " + stat_ci, cc, value)


print(datetime.now(), "post process cells. Nb=", len(cells))

# cells dict to values list
cells = list(cells.values())

properties = ['GRD_ID', 'T', 'M', 'F', 'Y_LT15', 'Y_1564', 'Y_GE65', 'EMP', 'SAME', 'CHG_IN', 'CHG_OUT', 'NAT', 'EU_OTH', 'OTH', 'LAND_SURFACE', 'POPULATED']
cells_ = []
for cell in cells:

    # check all values are provided. Otherwise, set to 'not available'
    t = cell.get("T")
    for stat in properties:
        if stat not in cell:
            cell[stat] = 0 if t==0 else na_value

    # sort country codes in cell
    cell["CNTR_ID"] = "-".join(sorted(cell["CNTR_ID"]))

    # sort cell properties
    cell = {k: cell[k] for k in properties if k in cell}

    # store new ordered cells
    cells_.append(cell)

#
cells = cells_

print(datetime.now(), "store as geopackage")
grid_to_geopackage(cells, output_path + "census_grid_2021.gpkg", grid_resolution=1000)

print(datetime.now(), "store as csv")
with open(output_path + "census_grid_2021.csv", "w") as f:
    writer = csv.DictWriter(f, fieldnames=cells[0].keys())
    writer.writeheader()
    writer.writerows(cells)

print(datetime.now(), "store as parquet")
pq.write_table(pa.Table.from_pylist(cells), output_path + "census_grid_2021.parquet")

#TODO to geotiff

