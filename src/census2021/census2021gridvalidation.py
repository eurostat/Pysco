import csv

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import loadFeatures,keepOnlyGeometry
from utils.geomutils import average_z_coordinate
from utils.csvutils import save_as_csv


grid_path = "/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg"
bbox = [4200000, 2700000, 4560000, 3450000] #LU
output_folder = "/home/juju/gisco/census_2021_validation/"

#prepare output
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

    #check CI_XXX values
    for att in [ 'T_CI', 'M_CI', 'F_CI', 'Y_LT15_CI', 'Y_1564_CI', 'Y_GE65_CI', 'EMP_CI', 'NAT_CI', 'EU_OTH_CI', 'OTH_CI', 'SAME_CI', 'CHG_IN_CI', 'CHG_OUT_CI']:
        ci = c[att]
        if ci==None or ci==-9999: continue
        err_codes.append(att+"_value="+str(ci))

    #check consitency CI_XXX and XXX
    for att in ['T','M', 'F', 'Y_LT15', 'Y_1564', 'Y_GE65', 'EMP', 'NAT', 'EU_OTH', 'OTH', 'SAME', 'CHG_IN', 'CHG_OUT']:
        v = c[att]
        ci = c[att+"_CI"]
        if ci==-9999 and v==-9999: continue
        if ci==None and v>=0: continue
        err_codes.append(att+"_CI_inconsistency_ci="+str(ci)+"_value="+str(v))

    #check POPULATED values
    att = 'POPULATED'
    v = c[att]
    if v != 0 and v != 1: err_codes.append(att+"_value="+str(v))

    #check consitency POPULATED and T
    if v==1 and c['T']<=0: err_codes.append("POPULATED_T_inconsistency="+str(v)+"_"+str(c['T']))
    if v==0 and c['T']>0: err_codes.append("POPULATED_T_inconsistency="+str(v)+"_"+str(c['T']))

    #check valid population values
    for att in ['T','M', 'F', 'Y_LT15', 'Y_1564', 'Y_GE65', 'EMP', 'NAT', 'EU_OTH', 'OTH', 'SAME', 'CHG_IN', 'CHG_OUT']:
        v = c[att]
        if v == None or v>=0 or v==-9999: continue
        err_codes.append(att+"_neg="+str(v))

    #check categrories sum up to total
    #TODO

    #errors detected
    if len(err_codes) > 0:
        err = {'GRD_ID':c['GRD_ID'], 'errors': ",".join(err_codes)}
        errors.append(err)






#TODO move
def csv_grid_to_geopackage(csv_grid_path, gpkg_grid_path, geom="surf"):

    #load csv
    data = None
    with open(csv_grid_path, mode="r", newline="") as file:
        reader = csv.DictReader(file)
        data = list(reader)

    for row in data:
        print(row)

        #make cell
        c = {"type":"Feature", "properties":{}}
        p = c["properties"]

        #make grid cell geometry
        cell_geometry = Polygon([(x, y), (x+grid_resolution, y), (x+grid_resolution, y+grid_resolution), (x, y+grid_resolution)])
        #cell geometry
        c["geometry"] = mapping(cell_geometry)

    schema = get_schema_from_feature(cells[0])
    out = fiona.open(out_folder+out_file+".gpkg", 'w', driver='GPKG', crs=CRS.from_epsg(crs), schema=schema)
    out.writerecords(cells)






print(len(errors), "errors found")

if len(errors)>0:
    #sort by error
    errors = sorted(errors, key=lambda x: x["errors"])
    print("Save to ", output_folder + "errors.csv")
    save_as_csv(output_folder + "errors.csv", errors)

    print("Save to ", output_folder + "errors.gpkg")
    csv_grid_to_geopackage(output_folder + "errors.csv", output_folder + "errors.gpkg")


