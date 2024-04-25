import geopandas as gpd
from shapely.geometry import Polygon,box
from datetime import datetime
from math import ceil,isnan
import concurrent.futures

import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from lib.utils import cartesian_product_comp


file_path = '/home/juju/geodata/FR/BDTOPO_3-3_TOUSTHEMES_GPKG_LAMB93_R44_2023-12-15/BDT_3-3_GPKG_3035_R44-ED2023-12-15.gpkg'
out_folder = '/home/juju/gisco/building_demography/'
#minx = 3800000; maxx = 4200000; miny = 2700000; maxy = 3000000
minx = 3900000; maxx = 3950000; miny = 2800000; maxy = 2850000
#bbox = box(minx, miny, maxx, maxy)

num_processors_to_use = 8
resolution = 1000
partition_size = 10000


nb_floors_fr_fun = lambda f: 1 if f.hauteur==None or isnan(f.hauteur) else ceil(f.hauteur/3.7)
residential_fr_fun = lambda f: 1 if f.usage_1=="Résidentiel" else 0.3 if f.usage_2=="Résidentiel" else 0.1 if f.usage_1=="Indifférencié" else 0
cultural_value_fr_fun = lambda f: 1 if f.usage_1=="Religieux" or f.nature=="Tour, donjon" or f.nature=="Monument" or f.nature=="Moulin à vent" or f.nature=="Arc de triomphe" or f.nature=="Fort, blockhaus, casemate" or f.nature=="Eglise" or f.nature=="Château" or f.nature=="Chapelle" or f.nature=="Arène ou théâtre antique" else 0

cell_geometries = []
tot_nbs = []
tot_ground_areas = []
tot_floor_areas = []
tot_res_floor_areas = []
tot_cult_ground_areas = []
tot_cult_floor_areas = []
grd_ids = []


def proceed_partition(xy):
    [x_,y_] = xy

    print(datetime.now(), x_, y_, "load buildings")
    buildings = gpd.read_file(file_path, layer='batiment', bbox=box(x_, y_, x_+partition_size, y_+partition_size))
    print(datetime.now(), x_, y_, len(buildings))
    if len(buildings)==0: return

    #print(datetime.now(), "spatial index buildings")
    buildings.sindex

    for x in range(x_, x_+partition_size, resolution):
        for y in range(y_, y_+partition_size, resolution):

            #make grid cell geometry
            cell_geometry = Polygon([(x, y), (x+resolution, y), (x+resolution, y+resolution), (x, y+resolution)])

            #get buildings intersecting cell, using spatial index
            buildings_ = buildings.sindex.intersection(cell_geometry.bounds)
            if len(buildings_)==0: continue

            #initialise totals
            tot_nb = 0
            tot_ground_area = 0
            tot_floor_area = 0
            tot_res_floor_area = 0
            tot_cult_ground_area = 0
            tot_cult_floor_area = 0

            #go through buildings
            for i_ in buildings_:
                bu = buildings.iloc[i_]
                if not cell_geometry.intersects(bu.geometry): continue
                a = cell_geometry.intersection(bu.geometry).area
                if a == 0: continue

                #building number
                nb = a/bu.geometry.area
                if nb>1: nb=1
                tot_nb += nb

                #building area
                tot_ground_area += a
                floor_area = a * nb_floors_fr_fun(bu)
                tot_floor_area += floor_area

                #residential buildings
                tot_res_floor_area += residential_fr_fun(bu) * floor_area

                #cultural buildings
                cult = cultural_value_fr_fun(bu)
                tot_cult_ground_area += cult * a
                tot_cult_floor_area += cult * floor_area

            #round values
            tot_ground_area = round(tot_ground_area)
            tot_floor_area = round(tot_floor_area)
            tot_res_floor_area = round(tot_res_floor_area)
            tot_cult_ground_area = round(tot_cult_ground_area)
            tot_cult_floor_area = round(tot_cult_floor_area)

            if(tot_ground_area == 0): continue

            #store cell values
            cell_geometries.append(cell_geometry)
            tot_nbs.append(tot_nb)
            tot_ground_areas.append(tot_ground_area)
            tot_floor_areas.append(tot_floor_area)
            tot_res_floor_areas.append(tot_res_floor_area)
            tot_cult_ground_areas.append(tot_cult_ground_area)
            tot_cult_floor_areas.append(tot_cult_floor_area)

            #cell code
            grd_ids.append("CRS3035RES"+str(resolution)+"mN"+str(int(y))+"E"+str(int(x)))

#proceed_partition([3900000, 2800000])

#launch parallel computation   
with concurrent.futures.ThreadPoolExecutor(max_workers=num_processors_to_use) as executor:
    executor.map(proceed_partition, cartesian_product_comp(minx, miny, maxx, maxy, partition_size))

print(datetime.now(), "save grid as GPKG", len(cell_geometries))
buildings = gpd.GeoDataFrame({'geometry': cell_geometries, 'GRD_ID': grd_ids, 'number': tot_nbs, 'ground_area': tot_ground_areas, 'floor_area': tot_floor_areas, 'residential_floor_area': tot_res_floor_areas, 'cultural_ground_area': tot_cult_ground_areas, 'cultural_floor_area': tot_cult_floor_areas })
buildings.crs = 'EPSG:3035'
buildings.to_file(out_folder+"bu_dem_grid.gpkg", driver="GPKG")

print(datetime.now(), "save grid as CSV", len(cell_geometries))
buildings = buildings.drop(columns=['geometry'])
buildings.to_csv(out_folder+"bu_dem_grid.csv", index=False)
