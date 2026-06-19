import os

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.csvutils import hypercube_csv_to_timeseries_csv



in_folder = "/home/juju/gisco/accessibility/stats/"
service = "evrp"
geo = "NUTS_2024"
hypercube_csv_to_timeseries_csv(in_folder + "euro_access_"+service+"_"+geo+".csv", in_folder + "decomposed/",
                    output_file_name_fun = lambda f: "euro_access_"+service+"_"+geo+"__"+f)

