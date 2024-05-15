import os
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

    #iterate through cells
    for c in csvreader:
        #set position
        position_fun(c)

        #get cell tile x,y
        xt = floor((c.x - xO) / tileSizeM)
        yt = floor((c.y - yO) / tileSizeM)

        #compute cell position within its tile
        c["x"] = floor((c["x"] - xO) / r - xt * tile_size_cell)
        c["y"] = floor((c["y"]- yO) / r - yt * tile_size_cell)

        #check x,y values. Should be within [0,tile_size_cell-1]
        if (c["x"] < 0): print("Too low value: " + c.x + " <0")
        if (c["y"] < 0): print("Too low value: " + c.y + " <0")
        if (c["x"] > tile_size_cell - 1): print("Too high value: " + c.x + " >" + (tile_size_cell - 1))
        if (c["y"] > tile_size_cell - 1): print("Too high value: " + c.y + " >" + (tile_size_cell - 1))

        #create folder
        folder = output_folder + "/" + xt + "/"
