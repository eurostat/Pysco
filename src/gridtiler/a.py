import csv
from math import floor

input_file = "/home/juju/gisco/building_demography/building_demography.csv"
output_folder = '/home/juju/Bureau/test_tiling'
r = 100
tile_size_cell = 128
xO = 3200000
yO = 1850000
crs = "3035"

#compute tile size, in geo unit
tileSizeM = r * tile_size_cell

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

        #get tile x,y
        xt = floor((c.x - xO) / tileSizeM)
        yt = floor((c.y - yO) / tileSizeM)
