import sys
import os
import csv
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.dasymetric_mapping import dasymetric_disaggregation_step_1, dasymetric_aggregation_step_2
from utils.gridutils import grid_to_geopackage


input_path = "/home/juju/geodata/census/2021/input20250123/"
output_path = "/home/juju/gisco/census_2021_production/"
confidential_value = -1
na_value = -999

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

#for cc in ["LU", "BE", "FR"]:
for cc in ["AT","BE","BG","CH","CY","CZ","DE","DK","EE","EL","ES","FI","FR","HR","HU","IE","IT","LI","LT","LU","LV","MT","NL","NO","PL","PT","RO","SE","SI","SK"]:

    print(datetime.now(), "process " + cc)

    with open(input_path + "CENSUS_GRID_N_" + cc + "_2021.csv") as f: #, newline="", encoding="utf-8"
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
            ls = row["LAND_SURFACE"]
            #TODO check that issue !
            # if cell.get("LAND_SURFACE") is not None and ls != cell.get("LAND_SURFACE"): print("unexpected different land surface value found for cell " + id +" "+cc+ ": " + str(cell.get("LAND_SURFACE")) + " vs " + ls)
            cell["LAND_SURFACE"] = ls

            # get row info
            stat = row["STAT"]
            stat_ci = row["SPECIAL_VALUE"]
            value = row["OBS_VALUE"]
            if value is None or value == "": value = 0
            value = int(value)

            # get previous cell value for that stat
            prv_value = cell.get(stat)
            # if previous cell value is confidential, keep it confidential, even if new value is not confidential
            if prv_value == confidential_value: continue

            # if new cell value confidential, set cell value to confidential
            if stat_ci == "confidential": cell[stat] = confidential_value
            # new cell value not confidential
            elif stat_ci == "":
                if prv_value is None:
                    cell[stat] = value
                else:
                    cell[stat] += value
            else:
                print("unexpected confidential value found: " + stat_ci)



print(datetime.now(), "post process cells. Nb=", len(cells))

# cells dict to values list
cells = list(cells.values())

properties = ['T', 'F', 'M', 'Y_LT15', 'Y15-64', 'Y_GE65', 'EMP', 'SAME', 'CHG_IN', 'CHG_OUT', 'NAT', 'EU_OTH', 'OTH', 'LAND_SURFACE']
for cell in cells:

    # check all values are provided. Otherwise, set to 'not available'
    t = cell.get("T")
    #print(t)
    for stat in properties:
        if stat not in cell:
            cell[stat] = 0 if t==0 else na_value

    # sort country codes in cell
    cell["CNTR_ID"] = "-".join(sorted(cell["CNTR_ID"]))

    # sort cell properties
    cell = {k: cell[k] for k in properties if k in cell}

print(datetime.now(), "store as geopackage")
grid_to_geopackage(cells, output_path + "census_grid_2021.gpkg", grid_resolution=1000)

print(datetime.now(), "store as csv")
with open(output_path + "census_grid_2021.csv", "w") as f: #, newline="", encoding="utf-8"
    writer = csv.DictWriter(f, fieldnames=cells[0].keys())
    writer.writeheader()
    writer.writerows(cells)
