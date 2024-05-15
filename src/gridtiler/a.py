import csv

input_file = "/home/juju/gisco/building_demography/building_demography.csv"
output_folder = '/home/juju/Bureau/test_tiling'
resolution = 100
tile_size_cell = 128
origin_x = 3200000
origin_y = 1850000
crs = "3035"


#set cell x,y from its grid_id
def position_fun(c):
    a = c['GRD_ID'].split("N")[1].split("E")
    c["x"] = int(a[1])
    c["y"] = int(a[0])
    del c['GRD_ID']


with open(input_file, 'r') as csvfile:
    csvreader = csv.DictReader(csvfile)
    #print(csvreader.fieldnames)
    for c in csvreader:
        position_fun(c)
        print(c)
