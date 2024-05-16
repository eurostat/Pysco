import os
import csv
from math import floor
import json


#TODO move to gridtiler repository

def grid_tiling(
    input_file,
    output_folder,
    resolution,
    tile_size_cell = 128,
    x_origin = 0,
    y_origin = 0,
    crs = ""
):

    #compute tile size, in geo unit
    tile_size_m = resolution * tile_size_cell

    #minimum and maximum tile x,x, for info.json file
    minTX=None
    maxTX=None
    minTY=None
    maxTY=None

    with open(input_file, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)
        csv_header = None

        #iterate through cells from the input CSV file
        for c in csvreader:

            #get cell tile x,y
            xt = int(floor((float(c["x"]) - x_origin) / tile_size_m))
            yt = int(floor((float(c["y"]) - y_origin) / tile_size_m))

            #store extreme positions, for info.json file
            if minTX == None or xt<minTX: minTX = xt
            if maxTX == None or xt>maxTX: maxTX = xt
            if minTY == None or yt<minTY: minTY = yt
            if maxTY == None or yt>maxTY: maxTY = yt

            #compute cell position within its tile
            c["x"] = int(floor((c["x"] - x_origin) / resolution - xt * tile_size_cell))
            c["y"] = int(floor((c["y"]- y_origin) / resolution - yt * tile_size_cell))

            #check x,y values. Should be within [0,tile_size_cell-1]
            if (c["x"] < 0): print("Too low value: " + c.x + " <0")
            if (c["y"] < 0): print("Too low value: " + c.y + " <0")
            if (c["x"] > tile_size_cell - 1): print("Too high value: " + c.x + " >" + (tile_size_cell - 1))
            if (c["y"] > tile_size_cell - 1): print("Too high value: " + c.y + " >" + (tile_size_cell - 1))

            #round floats to ints, when possible
            round_floats_to_ints(c)

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
            "x": x_origin,
            "y": y_origin
        },
        "resolutionGeo": resolution,
        "tilingBounds": {
            "yMin": minTY,
            "yMax": maxTY,
            "xMax": maxTX,
            "xMin": minTX
        }
    }

    with open(output_folder + '/info.json', 'w') as json_file:
        json.dump(data, json_file, indent=3)



#make csv header from a cell, starting with "x" and "y"
def get_csv_header(cell):
    keys = list(cell.keys())
    keys.remove("x")
    keys.remove("y")
    keys.insert(0, "x")
    keys.insert(1, "y")
    return keys

#convert rounded floats into ints so that we do not have useless ".0"
def round_floats_to_ints(cell):
    for key, value in cell.items():
        try:
            f = float(value)
            if f.is_integer(): cell[key] = int(f)
        except ValueError: pass
