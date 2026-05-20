import sys
import os
import csv
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.gridutils import grid_to_geopackage

input_path = "/home/juju/geodata/census/2021/input20250123/"
output_folder = "/home/juju/gisco/census_2021_v3_production/input_validation/"
os.makedirs(output_folder, exist_ok=True)


def validate_input(rule, out_path):

    # output cells, as dict indexed by cell_id
    cells = {}

    #for cc in ["AT","BE","BG","CH"]:
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

                # get row info
                stat = row["STAT"]
                if stat == "Y15-64": stat = "Y_1564"
                value = row["OBS_VALUE"]

                stat_ci = row["SPECIAL_VALUE"]

                # check confidential values
                if rule == "all" or rule == "values":
                    if value == "" or value is None or int(value)<0:
                        cell["ERROR_TYPE"].append("value")
                        cell["ERROR_MSG"].append("unexpected value found: " + stat + "=" + value)

                # check confidential values
                if rule == "all" or rule == "ci_values":
                    if stat_ci != "confidential" and stat_ci != "" and stat_ci != "notApplicable":
                        cell["ERROR_TYPE"].append("confidential_value")
                        cell["ERROR_MSG"].append("confidential value found: " + stat + ". conf=" + stat_ci)

                # check no value is provided for confidential cells
                if rule == "all" or rule == "consist_ci_value":
                    if stat_ci == "confidential" and value !="" and int(value) > 0:
                        cell["ERROR_TYPE"].append("non_zero_value_for_confidential")
                        cell["ERROR_MSG"].append("non zero value for confidential value: " + stat + "=" + value)


                # check land surface is within [0,1]
                if rule == "all" or rule == "land_surface_value":
                    lsu = row["LAND_SURFACE"]
                    if lsu == None or lsu == "": lsu = 0
                    lsu = float(lsu)
                    if lsu < 0 or lsu > 1:
                        cell["ERROR_TYPE"].append("invalid_land_surface_value")
                        cell["ERROR_MSG"].append("invalid land surface value: " + str(lsu))

                #TODO check that for all rows of a cell/cnt, lsu values are the same


                # populated

                # The flag ‘populated’ shall be applicable only to ‘total population’
                if stat == "T":
                    popu = row["POPULATED"]

                    # must be 0 or 1, or none
                    if rule == "all" or rule == "populated_values":
                        if popu != "0" and popu != "1":
                            cell["ERROR_TYPE"].append("unexpected_populated_value")
                            cell["ERROR_MSG"].append("unexpected POPULATED value found: " + popu + " with " + stat + "=" + value)

                    if rule == "all" or rule == "consist_populated_value":
                        # data items on total population with an observed value other than ‘0’ shall be marked with the flag ‘populated’;
                        if(value != "" and int(value) > 0 and popu != "1"):
                            cell["ERROR_TYPE"].append("non_zero_value_for_populated_cell")
                            cell["ERROR_MSG"].append("non zero value with POPULATED == 0: " + stat + "=" + value)
                        # data items on total population with an observed value ‘0’ shall not be marked with the flag ‘populated’. 
                        if((value == "0" or value == "") and popu != "0"):
                            cell["ERROR_TYPE"].append("zero_value_for_populated_cell")
                            cell["ERROR_MSG"].append("zero value with POPULATED > 0: " + stat + "=" + value)

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
    grid_to_geopackage(cells, out_path, grid_resolution=1000, ignore_errors=True)

    '''
    print(datetime.now(), "store as csv")
    with open(output_folder + "validation_input.csv", "w") as f:
        writer = csv.DictWriter(f, fieldnames=cells[0].keys())
        writer.writeheader()
        writer.writerows(cells)
    '''

for rule in ["values", "ci_values", "consist_ci_value", "land_surface_value", "populated_values", "consist_populated_value"]:
    print(datetime.now(), "validate rule", rule)
    validate_input(rule, output_folder + "validation_input" + rule + ".gpkg")

