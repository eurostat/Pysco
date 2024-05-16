import fiona
import csv
import os
from datetime import datetime
import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from gridtiler.gridtiler import grid_aggregation,grid_tiling

compilation = True
aggregation = True
tiling = True

gpkg_folder = '/home/juju/gisco/building_demography/out_partition/'

#working folder
folder = "/home/juju/gisco/building_demography/tmp/"
if not os.path.exists(folder): os.makedirs(folder)


if compilation:

    #make csv file
    with open(folder + "100.csv", 'w', newline='') as csvfile:
        writer = None

        #get all gpkg files to merge
        gpkg_files = os.listdir(gpkg_folder)

        #go through gpkg files
        for i, gpkg_file in enumerate(gpkg_files):
            print(datetime.now(), (i+1), "/", len(gpkg_files), gpkg_folder + gpkg_file)

            #open gpkg file
            with fiona.open(gpkg_folder + gpkg_file, 'r') as src:

                #write columns
                for feature in src:

                    #skip those with number <=0
                    if feature['properties']['number'] <= 0: continue

                    #get properties
                    properties = { key: value for key, value in feature['properties'].items() }

                    #grid_id to x,y
                    a = properties['GRD_ID'].split("N")[1].split("E")
                    properties["x"] = int(a[1])
                    properties["y"] = int(a[0])
                    del properties['GRD_ID']

                    #create writer and write header if not already done
                    if writer==None:
                        writer = csv.DictWriter(csvfile, fieldnames=properties.keys())
                        writer.writeheader()

                    #write
                    writer.writerow(properties)





#aggregation
aggregations = [2,5,10,20,50,100,200,500]
if aggregation:
    for a in aggregations:
        print("aggregation to", a*100, "m")
        grid_aggregation(folder+"100.csv", 100, folder+str(a*100)+'.csv', a)


#tiling
if tiling:
    for a in aggregations:
        resolution = a*100
        print("tiling for resolution", resolution)
        
        #create output folder
        out_folder = '/home/juju/workspace/BuildingDemography/pub/tiles/' + str(a*100)
        if not os.path.exists(folder): os.makedirs(folder)

        grid_tiling(
            folder+str(a*100)+'.csv',
            out_folder,
            resolution,
            #tile_size_cell = 128,
            x_origin = 2500000,
            y_origin = 1000000,
            crs = "EPSG:3035"
        )
