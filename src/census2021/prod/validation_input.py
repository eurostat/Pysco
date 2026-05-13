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

for cc in ["AT","BE","BG","CH","CY","CZ","DE","DK","EE","EL","ES","FI","FR","HR","HU","IE","IT","LI","LT","LU","LV","MT","NL","NO","PL","PT","RO","SE","SI","SK"]:

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

            # land surface
            v = row["LAND_SURFACE"]
            if cell.get("LAND_SURFACE") is not None and v != cell.get("LAND_SURFACE"):
                cell["ERROR_TYPE"].append("land_surface_mismatch")
                cell["ERROR_MSG"].append("different land surface value " + id +" "+cc+ ": " + str(cell.get("LAND_SURFACE")) + " vs " + v)
            cell["LAND_SURFACE"] = v

            # check populated
            v = row["POPULATED"]
            if cell.get("POPULATED") is not None and v != cell.get("POPULATED"):
                cell["ERROR_TYPE"].append("populated_mismatch")
                cell["ERROR_MSG"].append("different POPULATED value " + id +" "+cc+ ": " + str(cell.get("POPULATED")) + " vs " + v)
            cell["POPULATED"] = v

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

            # check populated
            popu = cell.get("POPULATED")
            if popu is None: popu = 1
            if popu not in [0,1]:
                cell["ERROR_TYPE"].append("populated_value")
                cell["ERROR_MSG"].append("POPULATED value found for cell " + id +" "+cc+ ": " + str(popu))
            elif(value > 0 and popu == 0):
                cell["ERROR_TYPE"].append("non_zero_value_for_populated_cell")
                cell["ERROR_MSG"].append("non zero value for cell with POPULATED == 0" + id +" "+cc+ ": " + stat + " = " + str(value))
            elif(value == 0 and popu == 1):
                cell["ERROR_TYPE"].append("zero_value_for_populated_cell")
                cell["ERROR_MSG"].append("zero value for cell with POPULATED > 0" + id +" "+cc+ ": " + stat + " = " + str(value))


            # check confidential values
            if stat_ci != "confidential" and stat_ci != "" and stat_ci != "notApplicable":
                cell["ERROR_TYPE"].append("confidential_value")
                cell["ERROR_MSG"].append("confidential value found: " + stat_ci + " for " + id + " in " + cc)



print(datetime.now(), "post process cells. Nb=", len(cells))

# cells dict to values list
cells = list(cells.values())

for cell in cells:
    cell["ERROR_TYPE"] = "-".join(cell["ERROR_TYPE"])
    cell["ERROR_MSG"] = " - ".join(cell["ERROR_MSG"])
    del cell["LAND_SURFACE"]
    del cell["POPULATED"]


print(datetime.now(), "store as geopackage")
grid_to_geopackage(cells, output_folder + "validation_input.gpkg", grid_resolution=1000, layer_name="validation_input")

print(datetime.now(), "store as csv")
with open(output_folder + "validation_input.csv", "w") as f:
    writer = csv.DictWriter(f, fieldnames=cells[0].keys())
    writer.writeheader()
    writer.writerows(cells)

