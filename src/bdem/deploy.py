import fiona
import csv
import os
from datetime import datetime
import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from gridtiler.gridtiler import grid_aggregation,grid_tiling

gpkg_folder = '/home/juju/gisco/building_demography/out_partition/'

#working folder
folder = "/home/juju/gisco/building_demography/tmp/"
if not os.path.exists(folder): os.makedirs(folder)


#make csv file
with open(folder + "100m", 'w', newline='') as csvfile:

    #get all gpkg files to merge
    gpkg_files = os.listdir(gpkg_folder)

    #go through gpkg files
    for i, gpkg_file in enumerate(gpkg_files):
        print(datetime.now(), (i+1), "/", len(gpkg_files), gpkg_folder + gpkg_file)

        #open gpkg file
        with fiona.open(gpkg_folder + gpkg_file, 'r') as src:

            #write header for the first one only
            if i==0:
                #write header
                schema = src.schema
                fieldnames = [field for field in schema['properties'].keys() if field != 'geometry']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

            #write columns
            for feature in src:

                #skip those with number <=0
                if feature['properties']['number'] <= 0: continue

                #get properties
                properties = {key: value for key, value in feature['properties'].items() if key != 'geometry'}

                #grid_id to x,y
                a = properties['GRD_ID'].split("N")[1].split("E")
                properties["x"] = int(a[1])
                properties["y"] = int(a[0])
                del properties['GRD_ID']

                #write
                writer.writerow(properties)




#aggregation
for a in [2,5,10,20,50,100,200,500]:
    print("aggregation to", a*100, "m")
    grid_aggregation(folder+"100.csv", 100, folder+str(a*100)+'.csv', a)


#tiling
for a in [1,2,5,10,20,50,100,200,500]:
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
