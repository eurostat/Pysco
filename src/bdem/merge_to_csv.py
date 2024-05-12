import fiona
import csv

# Path to the GeoPackage file
gpkg_file = '/home/juju/gisco/building_demography/out_partition/eurobudem_100m_4000000_2500000.gpkg'
csv_file = '/home/juju/gisco/building_demography/building_demography.csv'

with fiona.open(gpkg_file, 'r') as src:
   with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)        
        writer.writerow(['property1', 'property2'])

        for feature in src:
            number = feature['properties']['number']
            if number<=0: continue
            writer.writerow(["aaa", number])

