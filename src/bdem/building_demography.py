import fiona
from fiona.crs import CRS
from shapely.geometry import Polygon,box,shape,mapping
from datetime import datetime
import concurrent.futures

import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from utils.utils import cartesian_product_comp
from utils.featureutils import spatialIndex,get_schema_from_feature





def building_demography_grid(buildings_loader,
                             bbox,
                             out_folder,
                             out_file,
                             cell_id_fun=lambda x,y:str(x)+"_"+str(y),
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

        #out data
        cell_geometries = []
        tot_nbs = []
        tot_ground_areas = []
        tot_floor_areas = []
        tot_res_ground_areas = []
        tot_res_floor_areas = []
        tot_activity_ground_areas = []
        tot_activity_floor_areas = []
        tot_cult_ground_areas = []
        tot_cult_floor_areas = []
        grd_ids = []

        #make cells
        cells = []
        for x in range(x_part, x_part+partition_size, grid_resolution):
            for y in range(y_part, y_part+partition_size, grid_resolution):

                #make cell
                c = {"type":"Feature", "properties":{}}
                p = c["properties"]

                #make grid cell geometry
                cell_geometry = Polygon([(x, y), (x+grid_resolution, y), (x+grid_resolution, y+grid_resolution), (x, y+grid_resolution)])
                c["geometry"] = mapping(cell_geometry)

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

                    #building number
                    nb = ground_area/bug.area
                    if nb>1: nb=1
                    tot_nb += nb

                    #building area
                    tot_ground_area += ground_area
                    floor_area = ground_area * bu["floor_nb"]
                    tot_floor_area += floor_area

                    #residential buildings
                    resid = bu["residential"]
                    tot_res_ground_area += resid * ground_area
                    tot_res_floor_area += resid * floor_area

                    #economic activity buildings
                    activity = bu["activity"]
                    tot_activity_ground_area += activity * ground_area
                    tot_activity_floor_area += activity * floor_area

                    #cultural value buildings
                    cult = bu["cultural_value"]
                    tot_cult_ground_area += cult * ground_area
                    tot_cult_floor_area += cult * floor_area

                #skip empty cells
                if skip_empty_cells and tot_nb == 0: continue

                #round values
                tot_nb = round(tot_nb, 2)
                tot_ground_area = round(tot_ground_area)
                tot_floor_area = round(tot_floor_area)
                tot_res_ground_area = round(tot_res_ground_area)
                tot_res_floor_area = round(tot_res_floor_area)
                tot_activity_ground_area = round(tot_activity_ground_area)
                tot_activity_floor_area = round(tot_activity_floor_area)
                tot_cult_ground_area = round(tot_cult_ground_area)
                tot_cult_floor_area = round(tot_cult_floor_area)

                #store cell values
                cell_geometries.append(cell_geometry)
                tot_nbs.append(tot_nb)
                tot_ground_areas.append(tot_ground_area)
                tot_floor_areas.append(tot_floor_area)
                tot_res_ground_areas.append(tot_res_ground_area)
                tot_res_floor_areas.append(tot_res_floor_area)
                tot_activity_ground_areas.append(tot_activity_ground_area)
                tot_activity_floor_areas.append(tot_activity_floor_area)
                tot_cult_ground_areas.append(tot_cult_ground_area)
                tot_cult_floor_areas.append(tot_cult_floor_area)

                #store cell code
                p["GRD_ID"] = cell_id_fun(x,y)

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
        dst = fiona.open(out_folder+out_file+".gpkg", 'w', driver='GPKG', crs=CRS.from_epsg(crs), schema=schema)
        dst.writerecords(cells)
        #for f in cells: dst.write(f)

        print(datetime.now(), "Done")
