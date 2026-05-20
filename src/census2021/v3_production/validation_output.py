import sys
import os
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.featureutils import loadFeatures
from utils.csvutils import save_as_csv
from utils.gridutils import grid_to_geopackage

# input gpkg file to validate
grid_path = "/home/juju/gisco/census_2021_v3_production/ESTAT_Census_2021_V3.gpkg"
CONFIDENTIAL_VALUE = -8888
NA_VALUE = -9999

# output folder where to store the validation reports
output_folder = "/home/juju/gisco/census_2021_v3_production/output_validation/"
os.makedirs(output_folder, exist_ok=True)

# bounding box to focus on. Set to None for entire check
bbox = None #[4200000, 2700000, 4560000, 3450000] #LU


print(datetime.now(), "Load grid cells from", grid_path)
cells = loadFeatures(grid_path, bbox, load_geometry=False)
print(datetime.now(), len(cells), "cells loaded")


# 'GRD_ID', 'T',
# 'M', 'F', 
# 'Y_LT15', 'Y_1564', 'Y_GE65', 
# 'EMP', 
# 'NAT', 'EU_OTH', 'OTH', 
# 'SAME', 'CHG_IN', 'CHG_OUT', 
# 'LAND_SURFACE', 


# function to check the categories sum up to the total population
def check_categories_total(cell, categories, categories_label, err_codes):
    t = cell["T"]

    # check if any value of the categories is confidential or not available
    na = False
    for cat in categories:
        if cell[cat] != CONFIDENTIAL_VALUE and cell[cat] != NA_VALUE: continue
        na = True
        break

    # sum population figures by category
    sum = 0
    for cat in categories:
        v = cell[cat]
        if v==None or v==NA_VALUE or v==CONFIDENTIAL_VALUE: continue
        sum += v

    # if the sum is equal to the total, then OK
    if sum == t: return

    # if any of the values is confidential and the sum is lower than the total, then OK
    if na and sum <= t: return

    # report error
    err = categories_label + "_sum___T=" + str(t) + "_while_SUM=" + str(sum)
    err_codes.append(err)


# run validation of cells
def validation(cells, rules, file_name):

    # output errors
    errors = []

    for c in cells:
        # list of error codes for the cell
        err_codes = []

        # get total population
        t = c['T']

        # "data items on total population shall not be reported as confidential"
        if "ci_val" in rules:
            if c["T"] == CONFIDENTIAL_VALUE:
                err_codes.append("T value reported as confidential")

        # check valid population values: not none
        if "pop_values_none" in rules:
            for att in ['T','M', 'F', 'Y_LT15', 'Y_1564', 'Y_GE65', 'EMP', 'NAT', 'EU_OTH', 'OTH', 'SAME', 'CHG_IN', 'CHG_OUT']:
                if c[att] == None:
                    err_codes.append(att+"_none_value="+str(v))

        # check valid population values: not negative
        if "pop_values_non_neg" in rules:
            for att in ['T','M', 'F', 'Y_LT15', 'Y_1564', 'Y_GE65', 'EMP', 'NAT', 'EU_OTH', 'OTH', 'SAME', 'CHG_IN', 'CHG_OUT']:
                v = c[att]
                if v >= 0: continue
                if v == CONFIDENTIAL_VALUE: continue
                if v == NA_VALUE: continue
                if v == None: continue
                err_codes.append(att+"_negative_value="+str(v))

        # check EMP <= T
        if "emp_smaller_than_pop" in rules:
            emp = c['EMP']
            if(emp > t):
                err_codes.append("EMP_T_inconsistency_EMP="+str(emp)+"_T="+str(t))

        # check land_surface within [0,1]
        if "invalid_land_surface_value" in rules:
            lsu = float(c["LAND_SURFACE"])
            if lsu == NA_VALUE: continue
            if lsu < 0 or lsu > 1:
                err_codes.append("LAND_SURFACE_invalid_value="+str(lsu))

        # check cells with no land and with population: (land_surface <= 0) and (T != 0 or populated = 1)
        if "consist_land_population" in rules:
            lsu = float(c["LAND_SURFACE"])
            if lsu > 0: continue
            t = c["T"]
            if t <= 0: continue
            popu = c["POPULATED"]
            if popu <= 0: continue

            err_codes.append("POPULATION_without_LAND_SURFACE - LS="+str(lsu)+" T="+" POPULATED="+str(popu))

        # check POPULATED / T consistency
        if "consist_populated_t" in rules:
            t = c["T"]
            popu = c["POPULATED"]
            if t == 0 and popu == 0: continue
            if (t > 0 or t == CONFIDENTIAL_VALUE) and popu == 1: continue
            err_codes.append("Inconsistency populated/population. POPULATED="+str(popu)+" T="+str(t))


        # check categories sum up to total
        if "cat_sum_sex" in rules:
            check_categories_total(c, ['M', 'F'], "SEX", err_codes)
        if "cat_sum_age" in rules:
            check_categories_total(c, ['Y_LT15', 'Y_1564', 'Y_GE65'], "AGE", err_codes)
        if "cat_sum_cntbirth" in rules:
            check_categories_total(c, ['NAT', 'EU_OTH', 'OTH'], "CNTBIRTH", err_codes)
        if "cat_sum_reschange" in rules:
            check_categories_total(c, ['SAME', 'CHG_IN', 'CHG_OUT'], "RESCHANGE", err_codes)

        # errors detected
        if len(err_codes) > 0:
            di = {'GRD_ID':c['GRD_ID'], 'nb_errors': 0+len(err_codes), 'errors': ",".join(err_codes)}
            errors.append(di)

    print(datetime.now(), len(errors), "errors found")

    if len(errors)>0:

        #sort errors
        errors = sorted(errors, key=lambda c: c["errors"])

        #print(datetime.now(), "Save to ", output_folder + file_name + ".csv")
        #save_as_csv(output_folder + file_name + ".csv", errors)

        print(datetime.now(), "Save to ", output_folder + file_name + ".gpkg")
        grid_to_geopackage(errors, output_folder + file_name +".gpkg", layer_name = file_name, ignore_errors=True, grid_resolution=1000)





print(datetime.now(), "Run validation cell by cell...")

# list of rules
rules = ["ci_val", "pop_values_none", "pop_values_non_neg",
         "emp_smaller_than_pop", "invalid_land_surface_value", "consist_land_population", "consist_populated_t", "cat_sum_sex", "cat_sum_age", "cat_sum_cntbirth", "cat_sum_reschange"]

# one file per validation rule
for rule in rules:
    print(datetime.now(), rule)
    validation(cells, [rule], "errors_"+rule)

# all combined
print(datetime.now(), "all combined")
validation(cells, rules, "errors")

