import fiona
import csv
import os

csv_file = '/home/juju/gisco/building_demography/building_demography.csv'
gpkg_folder = '/home/juju/gisco/building_demography/out_partition/'
gpkg_files = os.listdir(gpkg_folder)

#open CSV file
with open(csv_file, 'w', newline='') as csvfile:

    for i, gpkg_file in enumerate(gpkg_files):
        print(gpkg_folder + gpkg_file)
        with fiona.open(gpkg_folder + gpkg_file, 'r') as src:

            if i==0:
                #write header
                schema = src.schema
                fieldnames = [field for field in schema['properties'].keys() if field != 'geometry']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

            #write columns
            for feature in src:

                #skip those with number <=0
                if feature['properties']['number'] <= 0: continue

                #write properties
                properties = {key: value for key, value in feature['properties'].items() if key != 'geometry'}
                writer.writerow(properties)
