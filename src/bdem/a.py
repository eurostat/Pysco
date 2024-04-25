import geopandas as gpd
from math import ceil,isnan
from building_demography import building_demography_grid


# FR bd topo


buildings_loader = lambda bbox: gpd.read_file('/home/juju/geodata/FR/BDTOPO_3-3_TOUSTHEMES_GPKG_LAMB93_R44_2023-12-15/BDT_3-3_GPKG_3035_R44-ED2023-12-15.gpkg', layer='batiment', bbox=bbox)
nb_floors_fun = lambda f: 1 if f.hauteur==None or isnan(f.hauteur) else ceil(f.hauteur/3.7)
residential_fun = lambda f: 1 if f.usage_1=="Résidentiel" else 0.3 if f.usage_2=="Résidentiel" else 0.1 if f.usage_1=="Indifférencié" else 0
cultural_value_fun = lambda f: 1 if f.usage_1=="Religieux" or f.nature=="Tour, donjon" or f.nature=="Monument" or f.nature=="Moulin à vent" or f.nature=="Arc de triomphe" or f.nature=="Fort, blockhaus, casemate" or f.nature=="Eglise" or f.nature=="Château" or f.nature=="Chapelle" or f.nature=="Arène ou théâtre antique" else 0

building_demography_grid(
    buildings_loader,
    [3800000, 2700000, 4200000, 3000000],
    #[4000000, 2800000, 4050000, 2850000],
    '/home/juju/gisco/building_demography/',
    "bu_dem_fr_bdtopo_grid",
    resolution=1000,
    partition_size = 50000,
    nb_floors_fun=nb_floors_fun,
    residential_fun=residential_fun,
    cultural_value_fun=cultural_value_fun,
    num_processors_to_use = 8
) 


# FR OSM
buildings_loader = lambda bbox: gpd.read_file('/home/juju/geodata/OSM/FR/buildings_grand_est.gpkg', bbox=bbox)
nb_floors_fun = lambda f: 1
residential_fun = lambda f: 0
cultural_value_fun = lambda f: 0

building_demography_grid(
    buildings_loader,
    [3800000, 2700000, 4200000, 3000000],
    #[4000000, 2800000, 4050000, 2850000],
    '/home/juju/gisco/building_demography/',
    "bu_dem_fr_osm_grid",
    resolution=1000,
    partition_size = 50000,
    nb_floors_fun=nb_floors_fun,
    residential_fun=residential_fun,
    cultural_value_fun=cultural_value_fun,
    num_processors_to_use = 8
) 
