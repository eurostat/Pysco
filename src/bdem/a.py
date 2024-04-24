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

cell_geometries = []
tot_floor_areas = []
tot_ground_areas = []
resolution = 200
for x in range(minx, maxx, resolution):
    for y in range(miny, maxy, resolution):

        #load buildings intersecting the cell
        buildings = gpd.read_file(file_path, layer='batiment', bbox=box(x, y, x+resolution, y+resolution))
        if len(buildings)==0: continue

        print(datetime.now(), x,y, len(buildings), "buildings")

        #make grid cell geometry
        cell_geometry = Polygon([(x, y), (x+resolution, y), (x+resolution, y+resolution), (x, y+resolution)])

        #initialise totals
        tot_floor_area = 0
        tot_ground_area = 0

        #go through buildings
        for iii,bu in buildings.iterrows():
            if not cell_geometry.intersects(bu.geometry): continue
            a = cell_geometry.intersection(bu.geometry).area
            if a == 0: continue
            tot_ground_area =+ a
            tot_floor_area += a * nb_floors_fun(bu)

        tot_ground_area = round(tot_ground_area)
        tot_floor_area = round(tot_floor_area)

        if(tot_ground_area == 0): continue

        cell_geometries.append(cell_geometry)
        tot_ground_areas.append(tot_ground_area)
        tot_floor_areas.append(tot_floor_area)


print(datetime.now(), "save grid", len(cell_geometries))
buildings = gpd.GeoDataFrame({'geometry': cell_geometries, 'ground_area': tot_ground_areas, 'floors_area': tot_floor_areas })
buildings.crs = 'EPSG:3035'
buildings.to_file(out_folder+"bu_dem_grid.gpkg", driver="GPKG")
