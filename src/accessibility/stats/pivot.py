import os

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.csvutils import hypercube_csv_to_timeseries_csv



in_folder = "/home/juju/gisco/accessibility/stats/"
out_folder = in_folder + "decomposed/"
service = "evrp"
geo = "NUTS_2024"

hypercube_csv_to_timeseries_csv(
    in_folder + "euro_access_"+service+"_"+geo+".csv",
    out_folder,
    output_file_name_fun = lambda f: "euro_access_"+service+"_"+geo+"__"+f)

# delete NR files (not usefull)
for filename in os.listdir(out_folder):
    if "__UNIT_NR__" in filename: os.remove(os.path.join(out_folder, filename))
