

import os

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.gridutils import gpkg_point_to_csv

#
services_path = "/home/juju/geodata/gisco/basic_services/"
version_tag = "20260421"


if not os.path.exists("tmp/"): os.makedirs("tmp/")
for service in ["education","healthcare"]:
    for year in ["2020", "2023"]:
        print(service, year)

        gpkg_point_to_csv(services_path + service + "_" + year + "_3035_" + version_tag + ".gpkg",
                          "tmp/" + service + "_" + year + "_3035_" + version_tag + ".csv",
                          attributes_to_keep=["name" if service == "education" else "hospital_name"],
                          rounding_precision=0)

