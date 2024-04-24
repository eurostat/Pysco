import geopandas as gpd
from shapely.geometry import Polygon,box
from datetime import datetime
from math import ceil,isnan


file_path = '/home/juju/geodata/FR/BDTOPO_3-3_TOUSTHEMES_GPKG_LAMB93_R44_2023-12-15/BDT_3-3_GPKG_3035_R44-ED2023-12-15.gpkg'
out_folder = '/home/juju/gisco/building_demography/'
#minx = 3830000; maxx = 4200000; miny = 2700000; maxy = 3025000
minx = 3880000; maxx = 3890000; miny = 2750000; maxy = 2790000
#bbox = box(minx, miny, maxx, maxy)

nb_floors_fun = lambda f: 1 if f.hauteur==None or isnan(f.hauteur) else ceil(f.hauteur/3.7)

cell_geoms = []
cell_tot_area = []
resolution = 1000
for x in range(minx, maxx, resolution):
    for y in range(miny, maxy, resolution):

        #load buildings
        gdf = gpd.read_file(file_path, layer='batiment', bbox=box(x, y, x+resolution, y+resolution))
        nb = len(gdf)
        if nb==0: continue

        print(datetime.now(), x,y, nb, "buildings")

        #make grid cell geometry
        cell_geom = Polygon([(x, y), (x+resolution, y), (x+resolution, y+resolution), (x, y+resolution)])

        tot_area = 0
        for iii,bu in gdf.iterrows():
            if not cell_geom.intersects(bu.geometry): continue
            inter = cell_geom.intersection(bu.geometry)
            if inter.area == 0: continue
            nb_floors = nb_floors_fun(bu)
            #ratio = inter.area/bu.geometry.area
            #if(ratio>1): ratio=1
            tot_area += inter.area * nb_floors
        tot_area = round(tot_area)

        cell_geoms.append(cell_geom)
        cell_tot_area.append(tot_area)


