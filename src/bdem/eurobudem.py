import fiona
from math import ceil,isnan,floor
from building_demography import building_demography_grid
from shapely.geometry import shape

#TODO
# migrate to fiona for loading
# date of creation
# other countries: NL, BE, PL, IT... see eubc
# other years


bbox = [3000001, 3000001, 3000001, 3000001]
#bbox = [3000000, 2000000, 4313621, 3162995]
grid_resolution = 100
file_size_m = 500000
out_folder = '/home/juju/gisco/building_demography/out_partition/'

clamp = lambda v:floor(v/file_size_m)*file_size_m
[xmin,ymin,xmax,ymax] = [clamp(v) for v in bbox]


#TODO extract
def loadFeatures(file, bbox):
    features = []
    gpkg = fiona.open(file, 'r')
    data = list(gpkg.items(bbox=bbox))
    for d in data:
        d = d[1]
        f = { "geometry": shape(d['geometry']) }
        properties = d['properties']
        for key, value in properties.items(): f[key] = value
        features.append(f)
    return features


def loadBuildings(bbox):
    buildings = loadFeatures('/home/juju/geodata/FR/BD_TOPO/BATI/batiment_3035.gpkg', bbox)
    #TODO format
    return buildings


for x in range(xmin, xmax+1, file_size_m):
    for y in range(ymin, ymax+1, file_size_m):
        print(x,y)

        building_demography_grid(
            loadBuildings,
            [x, y, x+file_size_m, y+file_size_m],
            out_folder,
            "eurobudem_" + str(grid_resolution) + "m_" + str(x) + "_" + str(y),
            cell_id_fun = lambda x,y: "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x)),
            grid_resolution = grid_resolution,
            partition_size = 100000,
            nb_floors_fun = lambda f: 1 if f.hauteur==None or isnan(f.hauteur) else ceil(f.hauteur/3),
            residential_fun = lambda f: 1 if f.usage_1=="Résidentiel" else 0.3 if f.usage_2=="Résidentiel" else 0.1 if f.usage_1=="Indifférencié" else 0,
            economic_activity_fun = lambda f: 1 if f.usage_1=="Agricole" or f.usage_1=="Commercial et services" or f.usage_1=="Industriel" else 0.3 if f.usage_2=="Agricole" or f.usage_2=="Commercial et services" or f.usage_2=="Industriel" else 0.1 if f.usage_1=="Indifférencié" else 0,
            cultural_value_fun = lambda f: 1 if f.usage_1=="Religieux" or f.nature=="Tour, donjon" or f.nature=="Monument" or f.nature=="Moulin à vent" or f.nature=="Arc de triomphe" or f.nature=="Fort, blockhaus, casemate" or f.nature=="Eglise" or f.nature=="Château" or f.nature=="Chapelle" or f.nature=="Arène ou théâtre antique" else 0,
            num_processors_to_use = 8
        ) 
