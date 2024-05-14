import fiona
from fiona.crs import CRS
from shapely.geometry import Polygon,box,shape,mapping
from datetime import datetime
import concurrent.futures

import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from utils.utils import cartesian_product_comp
from utils.featureutils import spatialIndex,get_schema_from_feature

cell_id_fun = lambda x, y, crs, resolution: "CRS"+str(crs)+"RES"+str(resolution)+"mN"+str(int(y))+"E"+str(int(x))


def building_demography_grid(buildings_loader,
                             bbox,
                             out_folder,
                             out_file,
                             grid_resolution=1000,
                             partition_size = 50000,
                             crs = 3035,
                             num_processors_to_use = 1,
                             skip_empty_cells = False
                             ):

    #process on a partition
    def proceed_partition(xy):
        [x_part, y_part] = xy

        print(datetime.now(), x_part, y_part, "load buildings")
        buildings = buildings_loader((x_part, y_part, x_part+partition_size, y_part+partition_size))
        print(datetime.now(), x_part, y_part, len(buildings), "buildings loaded")
        if len(buildings)==0: return

        #print(datetime.now(), "spatial index buildings")
        #buildings.sindex
        sindex = spatialIndex(buildings)
        #print(datetime.now(), "indexing done")

        #make cells
        cells = []
        for x in range(x_part, x_part+partition_size, grid_resolution):
            for y in range(y_part, y_part+partition_size, grid_resolution):

                #make cell
                c = {"type":"Feature", "properties":{}}
                p = c["properties"]

                #make grid cell geometry
                cell_geometry = Polygon([(x, y), (x+grid_resolution, y), (x+grid_resolution, y+grid_resolution), (x, y+grid_resolution)])

                #get buildings intersecting cell, using spatial index
                #buildings_ = buildings.sindex.intersection(cell_geometry.bounds)
                buildings_ = sindex.intersection(cell_geometry.bounds)
                #buildings_ = [feature_id for feature_id in buildings_]
                #if skip_empty_cells and len(buildings_)==0: continue

                #initialise totals
                p["number"] = 0
                p["ground_area"] = 0
                p["floor_area"] = 0
                p["residential_ground_area"] = 0
                p["residential_floor_area"] = 0
                p["economic_activity_ground_area"] = 0
                p["economic_activity_floor_area"] = 0
                p["cultural_ground_area"] = 0
                p["cultural_floor_area"] = 0

                #go through buildings
                for i_ in buildings_:
                    #bu = buildings.iloc[i_]
                    bu = buildings[i_]

                    bug = bu['geometry']
                    if not cell_geometry.intersects(bug): continue

                    bug = bug.buffer(0)
                    ground_area = cell_geometry.intersection(bug).area
                    if ground_area == 0: continue
                    floor_area = ground_area * bu["floor_nb"]

                    #building number
                    nb = ground_area/bug.area
                    if nb>1: nb=1
                    p["number"] += nb

                    #building area
                    p["ground_area"] += ground_area
                    p["floor_area"] += floor_area

                    #residential buildings
                    resid = bu["residential"]
                    p["residential_ground_area"] += resid * ground_area
                    p["residential_floor_area"] += resid * floor_area

                    #economic activity buildings
                    activity = bu["activity"]
                    p["economic_activity_ground_area"] += activity * ground_area
                    p["economic_activity_floor_area"] += activity * floor_area

                    #cultural value buildings
                    cult = bu["cultural_value"]
                    p["cultural_ground_area"] += cult * ground_area
                    p["cultural_floor_area"] += cult * floor_area

                #skip empty cells
                if skip_empty_cells and p["number"] == 0: continue

                #round values
                p["number"] = round(p["number"], 2)
                p["ground_area"] = round(p["ground_area"])
                p["floor_area"] = round(p["floor_area"])
                p["residential_ground_area"] = round(p["residential_ground_area"])
                p["residential_floor_area"] = round(p["residential_floor_area"])
                p["economic_activity_ground_area"] = round(p["economic_activity_ground_area"])
                p["economic_activity_floor_area"] = round(p["economic_activity_floor_area"])
                p["cultural_ground_area"]  = round(p["cultural_ground_area"])
                p["cultural_floor_area"] = round(p["cultural_floor_area"])

                #cell code
                p["GRD_ID"] = cell_id_fun(x, y, crs, grid_resolution)

                #cell geometry
                c["geometry"] = mapping(cell_geometry)

                #add new cell
                cells.append(c)

        return cells

    #launch parallel computation   
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_processors_to_use) as executor:
        partitions = cartesian_product_comp(bbox[0], bbox[1], bbox[2], bbox[3], partition_size)
        tasks_to_do = {executor.submit(proceed_partition, partition): partition for partition in partitions}

        # merge task outputs
        cells = []
        for task_output in concurrent.futures.as_completed(tasks_to_do):
            out = task_output.result()
            if(out==None): continue
            cells += out

        print(datetime.now(), len(cells), "cells")
        if(len(cells) == 0):
            print("No cell created")
            return

        print(datetime.now(), "save as GPKG")
        schema = get_schema_from_feature(cells[0])
        out = fiona.open(out_folder+out_file+".gpkg", 'w', driver='GPKG', crs=CRS.from_epsg(crs), schema=schema)
        out.writerecords(cells)

        print(datetime.now(), "Done")
