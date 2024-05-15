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
tile_size_m = r * tile_size_cell

#set cell x,y from its grid_id
def position_fun(c):
    a = c['GRD_ID'].split("N")[1].split("E")
    c["x"] = int(a[1])
    c["y"] = int(a[0])
    del c['GRD_ID']

#make list of keys from a cell, starting with "x" and "y"
def keys(cell):
    keys = cell.keys()
    keys.remove("x")
    keys.remove("y")
    keys.insert(0, "x")
    keys.insert(1, "y")
    return keys


with open(input_file, 'r') as csvfile:
    csvreader = csv.DictReader(csvfile)
    keys = None

    #iterate through cells
    for c in csvreader:
        #set position
        position_fun(c)

        #get cell tile x,y
        xt = int(floor((c["x"] - xO) / tile_size_m))
        yt = int(floor((c["y"] - yO) / tile_size_m))

        #compute cell position within its tile
        c["x"] = int(floor((c["x"] - xO) / r - xt * tile_size_cell))
        c["y"] = int(floor((c["y"]- yO) / r - yt * tile_size_cell))

        #check x,y values. Should be within [0,tile_size_cell-1]
        if (c["x"] < 0): print("Too low value: " + c.x + " <0")
        if (c["y"] < 0): print("Too low value: " + c.y + " <0")
        if (c["x"] > tile_size_cell - 1): print("Too high value: " + c.x + " >" + (tile_size_cell - 1))
        if (c["y"] > tile_size_cell - 1): print("Too high value: " + c.y + " >" + (tile_size_cell - 1))

        #create folder
        t_folder = output_folder + "/" + str(xt) + "/"
        if not os.path.exists(t_folder): os.makedirs(t_folder)

        file_path = t_folder + str(yt) + ".csv"
        file_exists = os.path.exists(file_path)
        with open(file_path, 'a', newline='') as csvfile:
            #writer
            if keys==None: keys = keys(c)
            writer = csv.DictWriter(csvfile, fieldnames=keys)
            #write header
            if not file_exists: writer.writeheader()
            #write cell data
            writer.writerow(c)

        #TODO: write info.json
