from math import ceil,isnan,floor
from building_demography import building_demography_grid
import rasterio

import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from utils.featureutils import loadFeatures,keepOnlyGeometry
from utils.geomutils import average_z_coordinate

#TODO
# other countries: IT, NL, BE, SK, CZ, PL... see eubc
# FR date of creation
# other years


#bbox = [5267541, 1749532, 5267541, 1749532] #IT small
#bbox = [4039813, 3004105, 4049813, 3094105] #LU north
#bbox = [4039813, 2954105, 4049813, 3094105] #LU-FR

bbox = [3500001, 2500001, 4400001, 3400001]
#bbox = [3000000, 2000000, 4413621, 3462995] #FR
grid_resolution = 100
file_size_m = 500000
out_folder = '/home/juju/gisco/building_demography/out_partition/'
num_processors_to_use = 5

clamp = lambda v:floor(v/file_size_m)*file_size_m
[xmin,ymin,xmax,ymax] = [clamp(v) for v in bbox]




def loadBuildings(bbox):
    buildings = []

    #FR
    buildings_FR = loadFeatures('/home/juju/geodata/FR/BD_TOPO/BATI/batiment_3035.gpkg', bbox)
    for bu in buildings_FR:
        bu["geometry"] = bu["geometry"].buffer(0)
        formatBuildingFR(bu)
    buildings += buildings_FR

    #LU
    buildings_LU = loadFeatures('/home/juju/geodata/LU/ACT/BDLTC_SHP/BATI/BATIMENT_3035.gpkg', bbox)
    for bu in buildings_LU:
        bu["geometry"] = bu["geometry"].buffer(0)
        formatBuildingLU(bu)
    buildings += buildings_LU

    #IT
    #TODO
    #edifc_uso edifc_ty edifc_at edifc_mon


    return buildings




DTM_LU = rasterio.open("/home/juju/geodata/LU/MNT_lux2017_3035.tif")
def formatBuildingLU(bu):
    n = bu["NATURE"]
    if n==None: n=0
    n = int(n)
    keepOnlyGeometry(bu)

    #estimate building height from geometry 'z' and DTM
    bu_top = average_z_coordinate(bu["geometry"])
    centroid = bu["geometry"].centroid
    row, col = DTM_LU.index(centroid.x, centroid.y)
    elevation = DTM_LU.read(1, window=((row, row+1), (col, col+1)))[0][0]
    h = bu_top - elevation

    bu["floor_nb"] = 1 if h==None or isnan(h) else max(ceil(h/3), 1)

    bu["residential"] = 1 if n==0 else 0
    bu["activity"] = 1 if (n>=10000 and n<42000) or n==80000 or n==11000 else 0
    bu["cultural_value"] = 1 if n in [41004,41005,41302,41303,41305] or (n>=50000 and n<=50011) else 0


def formatBuildingFR(bu):
    h = bu["hauteur"]
    u1 = bu["usage_1"]
    u2 = bu["usage_2"]
    n = bu["nature"]

    keepOnlyGeometry(bu)

    floor_nb = 1 if h==None or isnan(h) else ceil(h/3)
    bu["floor_nb"] = floor_nb
    residential = 1 if u1=="Résidentiel" else 0.3 if u2=="Résidentiel" else 0.25 if u1=="Indifférencié" else 0
    bu["residential"] = residential
    activity = 1 if u1=="Agricole" or u1=="Commercial et services" or u1=="Industriel" else 0.3 if u2=="Agricole" or u2=="Commercial et services" or u2=="Industriel" else 0.25 if u1=="Indifférencié" else 0
    bu["activity"] = activity
    cultural_value = 1 if u1=="Religieux" or n=="Tour, donjon" or n=="Monument" or n=="Moulin à vent" or n=="Arc de triomphe" or n=="Fort, blockhaus, casemate" or n=="Eglise" or n=="Château" or n=="Chapelle" or n=="Arène ou théâtre antique" else 0
    bu["cultural_value"] = cultural_value





for x in range(xmin, xmax+1, file_size_m):
    for y in range(ymin, ymax+1, file_size_m):
        print(x,y)

        building_demography_grid(
            loadBuildings,
            [x, y, x+file_size_m, y+file_size_m],
            out_folder,
            "eurobudem_" + str(grid_resolution) + "m_" + str(x) + "_" + str(y),
            grid_resolution = grid_resolution,
            partition_size = 100000,
            num_processors_to_use = num_processors_to_use,
            skip_empty_cells = True
        ) 
