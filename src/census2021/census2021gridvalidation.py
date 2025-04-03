
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import loadFeatures
from utils.csvutils import save_as_csv
from utils.gridutils import grid_to_geopackage

grid_path = "/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg"
bbox = [4200000, 2700000, 4560000, 3450000] #LU
output_folder = "/home/juju/gisco/census_2021_validation/"

#prepare output
os.makedirs(output_folder, exist_ok=True)

print("Load grid cells from", grid_path)
cells = loadFeatures(grid_path, bbox)
print(len(cells), "cells loaded")


#(['geometry', 'GRD_ID', 'T',
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
# 'SAME_CI', 'CHG_IN_CI', 'CHG_OUT_CI'])

print("Run validation cell by cell...")



#function to check the categories sum up to the total population
def check_categrories_total(cell, categories, categories_label, err_codes):
    t = cell["T"]

    #check if any value of the categories is confidential
    ci = False
    for cat in categories:
        if cell[cat+"_CI"] == 0: continue
        ci = True
        break

    #sum categories
    sum = 0
    for cat in categories:
        v = cell[cat]
        if v==None or v==-9999: continue
        sum += v

    #if the sum is equal to the total, then it is OK
    if sum==t: return

    #if any of the values is confidential and the sum is lower than the total, then it is OK
    if ci and sum<t: return

    #report error
    err = categories_label + "_sum_T=" + str(t) + "_SUM=" + str(sum)
    err_codes.append(err)


def validation(cells, rules, file_name):

    errors = []
    for c in cells:
        t = c['T']

        err_codes = []

        #check CI_XXX values
        if "ci_val" in rules:
            for att in [ 'T_CI', 'M_CI', 'F_CI', 'Y_LT15_CI', 'Y_1564_CI', 'Y_GE65_CI', 'EMP_CI', 'NAT_CI', 'EU_OTH_CI', 'OTH_CI', 'SAME_CI', 'CHG_IN_CI', 'CHG_OUT_CI']:
                ci = c[att]
                if ci==None: continue
                if ci==-9999: continue
                err_codes.append(att+"_value="+str(ci))

        #check consitency CI_XXX and XXX
        if "ci_consis" in rules:
            for att in ['T','M', 'F', 'Y_LT15', 'Y_1564', 'Y_GE65', 'EMP', 'NAT', 'EU_OTH', 'OTH', 'SAME', 'CHG_IN', 'CHG_OUT']:
                v = c[att]
                ci = c[att+"_CI"]
                if ci==-9999 and v==-9999: continue
                if ci==None and v !=None and v>=0: continue
                if att=="EMP" and ci==None and v==None: continue
                err_codes.append(att+"_CI_inconsistency_ci="+str(ci)+"_value="+str(v))

        #check POPULATED values
        if "populated_val" in rules:
            v = c['POPULATED']
            if v != 0 and v != 1: err_codes.append("POPULATED_value="+str(v))

        #check consitency POPULATED and T
        if "populated_consis" in rules:
            att = 'POPULATED'
            v = c['POPULATED']
            if v==1 and t<=0: err_codes.append("POPULATED_T_inconsistency_POPULATED="+str(v)+"_T="+str(t))
            if v==0 and t>0: err_codes.append("POPULATED_T_inconsistency_POPULATED="+str(v)+"_T="+str(t))

        #check valid population values
        if "pop_values" in rules:
            for att in ['T','M', 'F', 'Y_LT15', 'Y_1564', 'Y_GE65', 'EMP', 'NAT', 'EU_OTH', 'OTH', 'SAME', 'CHG_IN', 'CHG_OUT']:
                v = c[att]
                if v==-9999: continue
                if v!=None and v>=0: continue
                if att=="EMP" and v==None: continue
                err_codes.append(att+"_negative="+str(v))

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

    print(len(errors), "errors found")

    if len(errors)>0:

        #sort errors
        errors = sorted(errors, key=lambda c: c["errors"])

        print("Save to ", output_folder + file_name + ".csv")
        save_as_csv(output_folder + "errors.csv", errors)

        print("Save to ", output_folder + "errors.gpkg")
        grid_to_geopackage(errors, output_folder + file_name +".gpkg")





rules = ["ci_val", "ci_consis", "populated_val", "populated_consis", "pop_values", "emp_smaller_than_pop", "cat_sum_sex", "cat_sum_age", "cat_sum_cntbirth", "cat_sum_reschange"]
for rule in rules:
    print(rule)
    validation(cells, [rule], "errors_"+rule)

