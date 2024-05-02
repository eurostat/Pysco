import geopandas as gpd
from math import ceil,isnan
from building_demography import building_demography_grid



#bbox = [3800000, 2700000, 4200000, 3000000]
bbox = [4000000, 2800000, 4050000, 2850000]
partition_size = 10000
num_processors_to_use = 8
out_folder = '/home/juju/gisco/building_demography/'

# TODO
# activity: residential, industrial, agri, services, +activity
# gridviz - build_dem. for cult heritage
# date of construction

for case in ["BDTOPO"]:
    for grid_resolution in [100]:

        if(case == "BDTOPO"):
            print("FR BD Topo")
            building_demography_grid(
                lambda bbox: gpd.read_file('/home/juju/geodata/FR/BDTOPO_3-3_TOUSTHEMES_GPKG_LAMB93_R44_2023-12-15/BDT_3-3_GPKG_3035_R44-ED2023-12-15.gpkg', layer='batiment', bbox=bbox),
                bbox,
                out_folder,
                "bu_dem_grid_"+case+"_" + str(grid_resolution),
                grid_resolution = grid_resolution,
                partition_size = partition_size,
                nb_floors_fun = lambda f: 1 if f.hauteur==None or isnan(f.hauteur) else ceil(f.hauteur/3.7),
                residential_fun = lambda f: 1 if f.usage_1=="Résidentiel" else 0.3 if f.usage_2=="Résidentiel" else 0.1 if f.usage_1=="Indifférencié" else 0,
                cultural_value_fun = lambda f: 1 if f.usage_1=="Religieux" or f.nature=="Tour, donjon" or f.nature=="Monument" or f.nature=="Moulin à vent" or f.nature=="Arc de triomphe" or f.nature=="Fort, blockhaus, casemate" or f.nature=="Eglise" or f.nature=="Château" or f.nature=="Chapelle" or f.nature=="Arène ou théâtre antique" else 0,
                num_processors_to_use = num_processors_to_use
            ) 

        elif(case == "OSM"):

            print("OSM")
            building_demography_grid(
                lambda bbox: gpd.read_file('/home/juju/geodata/OSM/FR/buildings_grand_est.gpkg', bbox=bbox),
                bbox,
                out_folder,
                "bu_dem_grid_"+case+"_" + str(grid_resolution),
                grid_resolution = grid_resolution,
                partition_size = partition_size,
                nb_floors_fun = lambda f: 1,
                residential_fun = lambda f: 0,
                cultural_value_fun = lambda f: 0,
                num_processors_to_use = num_processors_to_use
            ) 
