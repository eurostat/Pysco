import geopandas as gpd
from math import ceil,isnan
from building_demography import building_demography_grid
import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from utils.osmutils import osm_building_floor_number

#TODO round building number to 2 decimals

bbox = [3900000, 2700000, 4200000, 3000000]
#bbox = [4000000, 2800000, 4100000, 2900000]

partition_size = 100000
num_processors_to_use = 9
cell_id_fun = lambda x,y: "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x))
out_folder = '/home/juju/gisco/building_demography/'

# TODO
# gridviz - build_dem. for cult heritage
# date of construction


for case in ["BDTOPO","OSM"]:
    for grid_resolution in [1000,100]:

        print("################", case, grid_resolution)

        if(case == "BDTOPO"):
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

        elif(case == "OSM"):
            building_demography_grid(
                lambda bbox: gpd.read_file('/home/juju/geodata/OSM/europe_road_buildings_prep.gpkg', bbox=bbox),
                bbox,
                out_folder,
                "bu_dem_grid_"+case+"_" + str(grid_resolution),
                cell_id_fun=cell_id_fun,
                grid_resolution = grid_resolution,
                partition_size = partition_size,
                nb_floors_fun = osm_building_floor_number,
                residential_fun = lambda f: 1 if f.building=="apartments" or f.building=="barracks" or f.building=="bungalow" or f.building=="cabin" or f.building=="detached" or f.building=="dormitory" or f.building=="farm" or f.building=="ger" or f.building=="farm" or f.building=="house" or f.building=="houseboat" or f.building=="residential" or f.building=="semidetached_house" or f.building=="static_caravan" or f.building=="stilt_house" or f.building=="terrace" or f.building=="tree_house" or f.building=="trullo" else 0.7 if f.building=="yes" else 0,
                economic_activity_fun = lambda f: 1 if f.building=="hotel" or f.building=="commercial" or f.building=="industrial" or f.building=="kiosk" or f.building=="office" or f.building=="retail" or f.building=="supermarket" or f.building=="warehouse" or f.building=="barn" or f.building=="conservatory" or f.building=="cowshed" or f.building=="farm_auxiliary" or f.building=="greenhouse" or f.building=="slurry_tank" or f.building=="stable" or f.building=="sty" or f.building=="livestock" or f.building=="civic" or f.building=="college" or f.building=="fire_station" or f.building=="hospital" or f.building=="government" or f.building=="kindergarten" or f.building=="museum" or f.building=="public" or f.building=="school" or f.building=="university" or f.building=="hangar" or f.building=="digester" or f.building=="service" or f.building=="tech_cab" or f.building=="transformer_tower" or f.building=="water_tower" or f.building=="storage_tank" or f.building=="silo" else 0.2 if f.building=="yes" else 0,
                cultural_value_fun = lambda f: 1 if f.building=="religious" or f.building=="cathedral" or f.building=="chapel" or f.building=="church" or f.building=="kingdom_hall" or f.building=="monastery" or f.building=="mosque" or f.building=="presbytery" or f.building=="shrine" or f.building=="synagogue" or f.building=="temple" or f.building=="pagoda" or f.building=="bunker" or f.building=="castle" or f.building=="tower" or f.building=="windmill" else 0,
                num_processors_to_use = num_processors_to_use
            ) 
