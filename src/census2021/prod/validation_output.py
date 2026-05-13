import sys
import os
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.featureutils import loadFeatures
from utils.csvutils import save_as_csv
from utils.gridutils import grid_to_geopackage

# input gpkg file to validate
grid_path = "/home/juju/gisco/census_2021_production/census_grid_2021.gpkg"
confidential_value = -8888
na_value = -9999

# output folder where to store the validation reports
output_folder = "/home/juju/gisco/census_2021_production/output_validation/"
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

# no longer:
# 'POPULATED', 
# 'T_CI', 
# 'M_CI', 'F_CI', 
# 'Y_LT15_CI', 'Y_1564_CI', 'Y_GE65_CI', 
# 'EMP_CI', 
# 'NAT_CI', 'EU_OTH_CI', 'OTH_CI', 
# 'SAME_CI', 'CHG_IN_CI', 'CHG_OUT_CI'


# function to check the categories sum up to the total population
def check_categories_total(cell, categories, categories_label, err_codes):
    t = cell["T"]

    # check if any value of the categories is confidential
    ci = False
    for cat in categories:
        if cell[cat] != confidential_value: continue
        ci = True
        break

    # sum population figures by category
    sum = 0
    for cat in categories:
        v = cell[cat]
        if v==None or v==na_value or v==confidential_value: continue
        sum += v

    # if the sum is equal to the total, then OK
    if sum == t: return

    # if any of the values is confidential and the sum is lower than the total, then OK
    if ci and sum <= t: return

    # report error
    err = categories_label + "_sum_T=" + str(t) + "_SUM=" + str(sum)
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
            if c["T"] == confidential_value:
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
                if v == confidential_value: continue
                if v == na_value: continue
                if v == None: continue
                err_codes.append(att+"_negative_value="+str(v))

        # check EMP <= T
        if "emp_smaller_than_pop" in rules:
            emp = c['EMP']
            if(emp > t):
                err_codes.append("EMP_T_inconsistency_EMP="+str(emp)+"_T="+str(t))

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

        print(datetime.now(), "Save to ", output_folder + file_name + ".csv")
        save_as_csv(output_folder + file_name + ".csv", errors)

        print(datetime.now(), "Save to ", output_folder + file_name + ".gpkg")
        grid_to_geopackage(errors, output_folder + file_name +".gpkg", layer_name = file_name)





print(datetime.now(), "Run validation cell by cell...")

# list of rules
rules = ["ci_val", "pop_values_none", "pop_values_non_neg",
         "emp_smaller_than_pop", "cat_sum_sex", "cat_sum_age", "cat_sum_cntbirth", "cat_sum_reschange"]

# one file per validation rule
for rule in rules:
    print(datetime.now(), rule)
    validation(cells, [rule], "errors_"+rule)

# all combined
validation(cells, rules, "errors")

