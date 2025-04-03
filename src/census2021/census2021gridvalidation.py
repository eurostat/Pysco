import csv

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import loadFeatures,keepOnlyGeometry
from utils.geomutils import average_z_coordinate


bbox = [4200000, 2700000, 4560000, 3450000] #LU
grid_path = "/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg"
output_folder = "/home/juju/gisco/census_2021_validation/"
os.makedirs(output_folder, exist_ok=True)

errors = []

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

for c in cells:
    err_codes = []

    #check valid population values
    for att in ['T','M', 'F', 'Y_LT15', 'Y_1564', 'Y_GE65', 'EMP', 'NAT', 'EU_OTH', 'OTH', 'SAME', 'CHG_IN', 'CHG_OUT']:
        v = c[att]
        if v == None: continue
        if v<0 and v!=-9999: err_codes.append(att+"neg="+str(v))

    #errors detected
    if len(err_codes) > 0:
        err = {'GRD_ID':c['GRD_ID'], 'code':err_codes}
        errors.append(err)


print(len(errors), "errors found")


out_filename = output_folder + "errors.csv"
print("save to ", out_filename)


def save_as_csv(csv_filename, data):
    with open(csv_filename, mode="w", newline="") as file:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

save_as_csv(out_filename, errors)

