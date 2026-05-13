import sys
import os
import csv
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.gridutils import grid_to_geopackage

input_path = "/home/juju/geodata/census/2021/input20250123/"
output_folder = "/home/juju/gisco/census_2021_production/input_validation/"
os.makedirs(output_folder, exist_ok=True)


# output cells, as dict indexed by cell_id
cells = {}

for cc in ["AT","BE","BG","CH"]:
#for cc in ["AT","BE","BG","CH","CY","CZ","DE","DK","EE","EL","ES","FI","FR","HR","HU","IE","IT","LI","LT","LU","LV","MT","NL","NO","PL","PT","RO","SE","SI","SK"]:

    print(datetime.now(), cc)

    with open(input_path + "CENSUS_GRID_N_" + cc + "_2021.csv") as f:
        rows = list(csv.DictReader(f))
        for row in rows:

            # get cell id
            id = row["SPATIAL"][3:]

            #
            if id == "unallocated": continue

            # get cell
            cell = cells.get(id)

            # no cell: create one
            if cell is None:
                cell = { "GRD_ID": id, "ERROR_TYPE": [], "ERROR_MSG" : [] }
                cells[id] = cell

            # get row info
            stat = row["STAT"]
            if stat == "Y15-64": stat = "Y_1564"
            stat_ci = row["SPECIAL_VALUE"]
            value = row["OBS_VALUE"]
            if value is None or value == "": value = 0
            value = int(value)

            # check no value is provided for confidential cells
            if stat_ci == "confidential" and value > 0:
                cell["ERROR_TYPE"].append("non_zero_value_for_confidential")
                cell["ERROR_MSG"].append("non zero value for confidential value " + id +" "+cc+ ": " + stat + " = " + str(value))

            # check populated value
            '''
            popu = cell.get("POPULATED")
            if popu is None or popu == "": popu = 0
            popu = float(popu)
            if popu != 0 and popu != 1:
                cell["ERROR_TYPE"].append("unexpected_populated_value")
                cell["ERROR_MSG"].append("unexpected POPULATED value found for cell " + id +" "+cc+ ": " + str(popu))
            '''

            '''
            elif(value > 0 and popu == 0):
                cell["ERROR_TYPE"].append("non_zero_value_for_populated_cell")
                cell["ERROR_MSG"].append("non zero value for cell with POPULATED == 0" + id +" "+cc+ ": " + stat + " = " + str(value))
            elif(value == 0 and popu == 1):
                cell["ERROR_TYPE"].append("zero_value_for_populated_cell")
                cell["ERROR_MSG"].append("zero value for cell with POPULATED > 0" + id +" "+cc+ ": " + stat + " = " + str(value))
            '''

            # check consitency populated/value
            '''
            #if ( stat == 'T' and popu == 1 and value == 0 ) or ( popu == 0 and value > 0 ):
            if stat == 'T' and popu == 1 and value == 0 :
                cell["ERROR_TYPE"].append("populated_mismatch")
                cell["ERROR_MSG"].append("inconsistent POPULATED value " + id +" "+cc+ ": " + str(popu) + " vs " + str(value) + " for stat " + stat)
            cell["POPULATED"] = v
            '''


            # check confidential values
            if stat_ci != "confidential" and stat_ci != "" and stat_ci != "notApplicable":
                cell["ERROR_TYPE"].append("confidential_value")
                cell["ERROR_MSG"].append("confidential value found: " + stat_ci + " for " + id + " in " + cc)



# cells dict to values list
cells = list(cells.values())

# keep only cells with errors
cells = [ cell for cell in cells if len(cell["ERROR_TYPE"]) > 0 ]

print(datetime.now(), "post process cells. Nb cells =", len(cells))


for cell in cells:
    cell["ERROR_TYPE"] = "-".join(cell["ERROR_TYPE"])
    cell["ERROR_MSG"] = " - ".join(cell["ERROR_MSG"])
    #del cell["POPULATED"]
    #cell["GRD_ID"] = cell["GRD_ID_"][3:]


print(datetime.now(), "store as geopackage")
grid_to_geopackage(cells, output_folder + "validation_input.gpkg", grid_resolution=1000, layer_name="validation_input")

'''
print(datetime.now(), "store as csv")
with open(output_folder + "validation_input.csv", "w") as f:
    writer = csv.DictWriter(f, fieldnames=cells[0].keys())
    writer.writeheader()
    writer.writerows(cells)
'''
