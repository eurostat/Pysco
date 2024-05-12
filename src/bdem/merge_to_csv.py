import fiona
import csv

# Path to the GeoPackage file
gpkg_file = '/home/juju/gisco/building_demography/out_partition/eurobudem_100m_4000000_2500000.gpkg'
csv_file = '/home/juju/gisco/building_demography/building_demography.csv'

with fiona.open(gpkg_file, 'r') as src:
    schema = src.schema
    fieldnames = [field for field in schema['properties'].keys() if field != 'geometry']
    with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for feature in src:
            number = feature['properties']['number']
            if number<=0: continue
            properties = {key: value for key, value in feature['properties'].items() if key != 'geometry'}
            writer.writerow(properties)
