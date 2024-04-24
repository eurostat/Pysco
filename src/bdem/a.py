import geopandas as gpd
from shapely.geometry import box
from datetime import datetime



file_path = '/home/juju/geodata/FR/BDTOPO_3-3_TOUSTHEMES_GPKG_LAMB93_R44_2023-12-15/BDT_3-3_GPKG_3035_R44-ED2023-12-15.gpkg'
out_folder = '/home/juju/gisco/building_demography/'
minx = 3830000
maxx = 4200000
miny = 2700000
maxy = 3025000
#bbox = box(minx, miny, maxx, maxy)

resolution = 1000
for x in range(minx, maxx, resolution):
    for y in range(miny, maxy, resolution):

        #load buildings
        gdf = gpd.read_file(file_path, layer='batiment', bbox=box(x, y, x+resolution, y+resolution))
        nb = len(gdf)
        if nb==0: continue

        print(datetime.now(), x,y, nb, "buildings")

