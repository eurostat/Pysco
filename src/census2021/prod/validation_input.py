import sys
import os
import csv
from datetime import datetime

input_path = "/home/juju/geodata/census/2021/input20250123/"
confidential_value = -8888
na_value = -9999

# output folder where to store the validation reports
output_folder = "/home/juju/gisco/census_2021_production/output_validation/"
os.makedirs(output_folder, exist_ok=True)


# output cells, as dict indexed by cell_id
cells = {}

errors = []

for cc in ["AT","BE","BG","CH","CY","CZ","DE","DK","EE","EL","ES","FI","FR","HR","HU","IE","IT","LI","LT","LU","LV","MT","NL","NO","PL","PT","RO","SE","SI","SK"]:

    print(datetime.now(), cc)

    with open(input_path + "CENSUS_GRID_N_" + cc + "_2021.csv") as f: #, newline="", encoding="utf-8"
        rows = list(csv.DictReader(f))
        for row in rows:

            # get cell id
            id = row["SPATIAL"][3:]

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
            #TODO check that issue !
            # if cell.get("LAND_SURFACE") is not None and v != cell.get("LAND_SURFACE"): print("unexpected different land surface value found for cell " + id +" "+cc+ ": " + str(cell.get("LAND_SURFACE")) + " vs " + v)
            cell["LAND_SURFACE"] = v

            # check populated
            #v = row["POPULATED"]
            #if cell.get("POPULATED") is not None and v != cell.get("POPULATED"): print("unexpected different POPULATED value found for cell " + id +" "+cc+ ": " + str(cell.get("POPULATED")) + " vs " + v)
            #cell["POPULATED"] = v

            # get row info
            stat = row["STAT"]
            if stat == "Y15-64": stat = "Y_1564"
            stat_ci = row["SPECIAL_VALUE"]
            value = row["OBS_VALUE"]
            if value is None or value == "": value = 0
            value = int(value)

            # check no value is provided for confidential cells
            if stat_ci == "confidential" and value > 0:
                print("unexpected non zero value for confidential value " + id +" "+cc+ ": " + stat + " = " + str(value))

            # check populated
            '''
            popu = cell.get("POPULATED")
            if popu is None: popu = 1
            if popu not in [0,1]:
                print("unexpected POPULATED value found for cell " + id +" "+cc+ ": " + str(popu))
            elif(value > 0 and popu == 0):
                print("unexpected non zero value for cell with POPULATED == 0" + id +" "+cc+ ": " + stat + " = " + str(value), popu)
            elif(value == 0 and popu == 1):
                print("unexpected zero value for cell with POPULATED > 0" + id +" "+cc+ ": " + stat + " = " + str(value), popu)
            '''

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

