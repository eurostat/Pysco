

services_path = "/home/juju/geodata/gisco/basic_services/"
version_tag = "v20260421"

for service in ["education","healthcare"]:
    for year in ["2020", "2023"]:
        path = services_path + service + "_" + year + "_3035_" + version_tag + ".gpkg"

        #open gpkg file and save as csv, keeping only the column "name" and "geometry"
        
