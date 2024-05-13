import geopandas as gpd
from shapely.geometry import Polygon,box,shape
from datetime import datetime
import concurrent.futures

import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from utils.utils import cartesian_product_comp
from utils.featureutils import spatialIndex



def building_demography_grid(buildings_loader,
                             bbox,
                             out_folder,
                             out_file,
                             cell_id_fun=lambda x,y:str(x)+"_"+str(y),
                             grid_resolution=1000,
                             partition_size = 50000,
                             crs = 'EPSG:3035',
                             num_processors_to_use = 1,
                             save_GPKG = True,
                             save_CSV = False,
                             save_parquet = False
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

        #go through cells
        for x in range(x_part, x_part+partition_size, grid_resolution):
            for y in range(y_part, y_part+partition_size, grid_resolution):

                #make grid cell geometry
                cell_geometry = Polygon([(x, y), (x+grid_resolution, y), (x+grid_resolution, y+grid_resolution), (x, y+grid_resolution)])

                #get buildings intersecting cell, using spatial index
                #buildings_ = buildings.sindex.intersection(cell_geometry.bounds)
                buildings_ = sindex.intersection(cell_geometry.bounds)
                #buildings_ = [feature_id for feature_id in buildings_]
                #if len(buildings_)==0: continue

                #initialise totals
                tot_nb = 0
                tot_ground_area = 0
                tot_floor_area = 0
                tot_res_ground_area = 0
                tot_res_floor_area = 0
                tot_activity_ground_area = 0
                tot_activity_floor_area = 0
                tot_cult_ground_area = 0
                tot_cult_floor_area = 0

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

                #if(tot_ground_area == 0): continue

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
                grd_ids.append(cell_id_fun(x,y))

        return [
            cell_geometries ,tot_nbs , tot_ground_areas , tot_floor_areas ,
            tot_res_ground_areas , tot_res_floor_areas , 
            tot_activity_ground_areas , tot_activity_floor_areas , 
            tot_cult_ground_areas , tot_cult_floor_areas , 
            grd_ids
        ]

    #launch parallel computation   
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_processors_to_use) as executor:
        partitions = cartesian_product_comp(bbox[0], bbox[1], bbox[2], bbox[3], partition_size)
        tasks_to_do = {executor.submit(proceed_partition, partition): partition for partition in partitions}

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

        # merge task outputs
        for task_output in concurrent.futures.as_completed(tasks_to_do):
            out = task_output.result()
            if(out==None): continue
            cell_geometries += out[0]
            tot_nbs += out[1]
            tot_ground_areas += out[2]
            tot_floor_areas += out[3]
            tot_res_ground_areas += out[4]
            tot_res_floor_areas += out[5]
            tot_activity_ground_areas += out[6]
            tot_activity_floor_areas += out[7]
            tot_cult_ground_areas += out[8]
            tot_cult_floor_areas += out[9]
            grd_ids += out[10]

        print(datetime.now(), len(cell_geometries), "cells")
        if(len(cell_geometries) == 0):
            print("No cell created")
            return

        #make output geodataframe
        out = gpd.GeoDataFrame({'geometry': cell_geometries, 'GRD_ID': grd_ids,
                                'number': tot_nbs, 'ground_area': tot_ground_areas, 'floor_area': tot_floor_areas,
                                'residential_ground_area': tot_res_ground_areas, 'residential_floor_area': tot_res_floor_areas,
                                'economic_activity_ground_area': tot_activity_ground_areas, 'economic_activity_floor_area': tot_activity_floor_areas,
                                'cultural_ground_area': tot_cult_ground_areas, 'cultural_floor_area': tot_cult_floor_areas })

        #save output

        if(save_GPKG):
            print(datetime.now(), "save as GPKG")
            out.crs = crs
            out.to_file(out_folder+out_file+".gpkg", driver="GPKG")

        if(save_CSV or save_parquet): out = out.drop(columns=['geometry'])

        if(save_CSV):
            print(datetime.now(), "save as CSV")
            out.to_csv(out_folder+out_file+".csv", index=False)
        if(save_parquet):
            print(datetime.now(), "save as parquet")
            out.to_parquet(out_folder+out_file+".parquet")
