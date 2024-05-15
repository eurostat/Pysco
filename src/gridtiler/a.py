import os
import csv
from math import floor
import json

input_file = "/home/juju/gisco/building_demography/building_demography.csv"
output_folder = '/home/juju/Bureau/test_tiling'
r = 100
tile_size_cell = 128
xO = 3200000
yO = 1850000
crs = "EPSG:3035"

#compute tile size, in geo unit
tile_size_m = r * tile_size_cell

#set cell x,y from its grid_id
def position_fun(c):
    a = c['GRD_ID'].split("N")[1].split("E")
    c["x"] = int(a[1])
    c["y"] = int(a[0])
    del c['GRD_ID']

#make csv header from a cell, starting with "x" and "y"
def get_csv_header(cell):
    keys = list(cell.keys())
    keys.remove("x")
    keys.remove("y")
    keys.insert(0, "x")
    keys.insert(1, "y")
    return keys

#minimum and maximum tile x,x, for info.json file
minTX=None
maxTX=None
minTY=None
maxTY=None

with open(input_file, 'r') as csvfile:
    csvreader = csv.DictReader(csvfile)
    csv_header = None

    #iterate through cells
    for c in csvreader:
        #set position
        position_fun(c)

        #get cell tile x,y
        xt = int(floor((c["x"] - xO) / tile_size_m))
        yt = int(floor((c["y"] - yO) / tile_size_m))

        #store extreme positions, for info.json file
        if minTX == None or xt<minTX: minTX = xt
        if maxTX == None or xt>maxTX: maxTX = xt
        if minTY == None or yt<minTY: minTY = yt
        if maxTY == None or yt>maxTY: maxTY = yt

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
            if csv_header==None: csv_header = get_csv_header(c)
            writer = csv.DictWriter(csvfile, fieldnames=csv_header)
            #write header
            if not file_exists: writer.writeheader()
            #write cell data
            writer.writerow(c)


#write info.json
data = {
    "dims": [],
    "crs": crs,
    "tileSizeCell": tile_size_cell,
    "originPoint": {
        "x": xO,
        "y": yO
    },
    "resolutionGeo": r,
    "tilingBounds": {
        "yMin": minTY,
        "yMax": maxTY,
        "xMax": maxTX,
        "xMin": minTX
    }
}

with open(output_folder + 'info.json', 'w') as json_file:
    json.dump(data, json_file, indent=3)
