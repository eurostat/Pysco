import sys
import os
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import loadFeatures
from utils.csvutils import save_as_csv
from utils.gridutils import grid_to_geopackage

# input gpkg file to validate
grid_path = "/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg"

#output folder where to store the validation reports
output_folder = "/home/juju/gisco/census_2021_validation/"
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
# 'POPULATED', 
# 'T_CI', 
# 'M_CI', 'F_CI', 
# 'Y_LT15_CI', 'Y_1564_CI', 'Y_GE65_CI', 
# 'EMP_CI', 
# 'NAT_CI', 'EU_OTH_CI', 'OTH_CI', 
# 'SAME_CI', 'CHG_IN_CI', 'CHG_OUT_CI'


#function to check the categories sum up to the total population
def check_categrories_total(cell, categories, categories_label, err_codes):
    t = cell["T"]

    #check if any value of the categories is confidential
    ci = False
    for cat in categories:
        if cell[cat+"_CI"] == 0: continue
        ci = True
        break

    #sum population figures by category
    sum = 0
    for cat in categories:
        v = cell[cat]
        if v==None or v==-9999: continue
        sum += v

    #if the sum is equal to the total, then OK
    if sum==t: return

    #if any of the values is confidential and the sum is lower than the total, then OK
    if ci and sum<=t: return

    #report error
    err = categories_label + "_sum_T=" + str(t) + "_SUM=" + str(sum)
    err_codes.append(err)


#run validation of cells
def validation(cells, rules, file_name):

    #output errors
    errors = []

    for c in cells:
        #list of error codes for the cell
        err_codes = []

        #get total population
        t = c['T']

        #check CI_XXX values: should be either None (non confidential) or -9999 (confidencial)
        #data items on total population shall not be reported as confidential;
        if "ci_val" in rules:
            for att in [ 'T_CI', 'M_CI', 'F_CI', 'Y_LT15_CI', 'Y_1564_CI', 'Y_GE65_CI', 'EMP_CI', 'NAT_CI', 'EU_OTH_CI', 'OTH_CI', 'SAME_CI', 'CHG_IN_CI', 'CHG_OUT_CI']:
                ci = c[att]
                if ci==None: continue
                if ci==-9999 and att!='T_CI': continue
                err_codes.append(att+"_value="+str(ci))

        #check consitency CI_XXX and XXX
        if "ci_consis" in rules:
            for att in ['T','M', 'F', 'Y_LT15', 'Y_1564', 'Y_GE65', 'EMP', 'NAT', 'EU_OTH', 'OTH', 'SAME', 'CHG_IN', 'CHG_OUT']:
                v = c[att]
                ci = c[att+"_CI"]
                #confidencial
                if ci==-9999 and v==-9999: continue
                #non confidential
                if ci==None and v!=-9999: continue
                #EMP special case, for FR and DE
                #if att=="EMP" and ci==None and v==None: continue
                err_codes.append(att+"_CI_inconsistency_ci="+str(ci)+"_value="+str(v))

        #check POPULATED values
        if "populated_val" in rules:
            v = c['POPULATED']
            if v != 0 and v != 1: err_codes.append("POPULATED_value="+str(v))


        #check consitency POPULATED and T
        if "populated_consis" in rules:
            p = c['POPULATED']
            # data items on total population with an observed value other than ‘0’ shall be marked with the flag ‘populated’
            if p==1 and t==0: err_codes.append("POPULATED_T_inconsistency_POPULATED="+str(p)+"_T="+str(t))
            # data items on total population with an observed value ‘0’ shall not be marked with the flag ‘populated’.
            if p==0 and t!=0: err_codes.append("POPULATED_T_inconsistency_POPULATED="+str(p)+"_T="+str(t))

        #check valid population values: not none
        if "pop_values_none" in rules:
            for att in ['T','M', 'F', 'Y_LT15', 'Y_1564', 'Y_GE65', 'EMP', 'NAT', 'EU_OTH', 'OTH', 'SAME', 'CHG_IN', 'CHG_OUT']:
                v = c[att]
                if v != None: continue
                #if att=="EMP": continue
                err_codes.append(att+"_none_value="+str(v))

        #check valid population values: not negative
        if "pop_values_non_neg" in rules:
            for att in ['T','M', 'F', 'Y_LT15', 'Y_1564', 'Y_GE65', 'EMP', 'NAT', 'EU_OTH', 'OTH', 'SAME', 'CHG_IN', 'CHG_OUT']:
                v = c[att]
                if v==-9999: continue
                if v==None: continue
                if v>=0: continue
                err_codes.append(att+"_negative_value="+str(v))


        #check EMP <= T
        if "emp_smaller_than_pop" in rules:
            emp = c['EMP']
            if(t != None and emp != None and emp>t):
                err_codes.append("EMP_T_inconsistency_EMP="+str(emp)+"_T="+str(t))

        #check categories sum up to total
        if "cat_sum_sex" in rules:
            check_categrories_total(c, ['M', 'F'], "SEX", err_codes)
        if "cat_sum_age" in rules:
            check_categrories_total(c, ['Y_LT15', 'Y_1564', 'Y_GE65'], "AGE", err_codes)
        if "cat_sum_cntbirth" in rules:
            check_categrories_total(c, ['NAT', 'EU_OTH', 'OTH'], "CNTBIRTH", err_codes)
        if "cat_sum_reschange" in rules:
            check_categrories_total(c, ['SAME', 'CHG_IN', 'CHG_OUT'], "RESCHANGE", err_codes)

        #errors detected
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
        grid_to_geopackage(errors, output_folder + file_name +".gpkg")





print(datetime.now(), "Run validation cell by cell...")

#list of rules
rules = ["ci_val", "ci_consis", "populated_val", "populated_consis", "pop_values_none", "pop_values_non_neg",
         "emp_smaller_than_pop", "cat_sum_sex", "cat_sum_age", "cat_sum_cntbirth", "cat_sum_reschange"]

#one file per validation rule
for rule in rules:
    print(datetime.now(), rule)
    validation(cells, [rule], "errors_"+rule)

#all combined
validation(cells, rules, "errors")
