import csv

input_file = "/home/juju/gisco/building_demography/building_demography.csv"
output_folder = '/home/juju/Bureau/test_tiling'
resolution = 100
tile_size_cell = 128
origin_x = 3200000
origin_y = 1850000
crs = "3035"

# --positionFunction "const a=c.GRD_ID.split('N')[1].split('E');return {x:a[1],y:a[0]};"
# --postFunction "delete c.GRD_ID"


with open(input_file, 'r') as csvfile:
    csvreader = csv.DictReader(csvfile)
    for row in csvreader:
        #pass
        print(row)
