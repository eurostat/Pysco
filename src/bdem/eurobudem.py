import geopandas as gpd
from math import ceil,isnan,floor
from building_demography import building_demography_grid
import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from utils.osmutils import osm_building_floor_number

#TODO round building number to 2 decimals

bbox = [3900000, 2700000, 4200000, 3000000]
#bbox = [4000000, 2800000, 4100000, 2900000]


partition_size = 100000
num_processors_to_use = 8
cell_id_fun = lambda x,y: "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))
out_folder = '/home/juju/gisco/building_demography/'


file_size_m = 500000
clamp = lambda v:floor(v/file_size_m)*file_size_m
[xmin,ymin,xmax,ymax] = [clamp(v) for v in bbox]

for x in range(x_part, x_part+partition_size, grid_resolution):
    for y in range(y_part, y_part+partition_size, grid_resolution):


building_demography_grid(
    lambda bbox: gpd.read_file('/home/juju/geodata/FR/BD_TOPO/BATI/batiment_3035.gpkg', bbox=bbox),
    bbox,
    out_folder,
    "bu_dem_grid_"+case+"_" + str(grid_resolution),
    cell_id_fun=cell_id_fun,
    grid_resolution = grid_resolution,
    partition_size = partition_size,
    nb_floors_fun = lambda f: 1 if f.hauteur==None or isnan(f.hauteur) else ceil(f.hauteur/3),
    residential_fun = lambda f: 1 if f.usage_1=="Résidentiel" else 0.3 if f.usage_2=="Résidentiel" else 0.1 if f.usage_1=="Indifférencié" else 0,
    economic_activity_fun = lambda f: 1 if f.usage_1=="Agricole" or f.usage_1=="Commercial et services" or f.usage_1=="Industriel" else 0.3 if f.usage_2=="Agricole" or f.usage_2=="Commercial et services" or f.usage_2=="Industriel" else 0.1 if f.usage_1=="Indifférencié" else 0,
    cultural_value_fun = lambda f: 1 if f.usage_1=="Religieux" or f.nature=="Tour, donjon" or f.nature=="Monument" or f.nature=="Moulin à vent" or f.nature=="Arc de triomphe" or f.nature=="Fort, blockhaus, casemate" or f.nature=="Eglise" or f.nature=="Château" or f.nature=="Chapelle" or f.nature=="Arène ou théâtre antique" else 0,
    num_processors_to_use = num_processors_to_use
) 
