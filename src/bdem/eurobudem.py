from math import ceil,isnan,floor
from building_demography import building_demography_grid
import rasterio

import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from utils.featureutils import loadFeatures,keepOnlyGeometry
from utils.geomutils import average_z_coordinate

#TODO
# join population from 1000m resolution OR disaggregate 2021 population and then join
# other countries: DK, SP, BE, SK, CZ, SI, FI... see eubc
# FR NL date of creation
# other years

#bbox = [3750000, 3250000, 4250000, 3250000] #NL
#bbox = [4750000, 2750000, 5250000, 3750000] #PL
#bbox = [4250000, 1250000, 5250000, 2750000] #IT
#bbox = [4267541, 2749532, 4267541, 3250000] #LU
#bbox = [3000000, 2000000, 4413621, 3462995] #FR

grid_resolution = 100
file_size_m = 500000
out_folder = '/home/juju/gisco/building_demography/out_partition/'
num_processors_to_use = 6

clamp = lambda v:floor(v/file_size_m)*file_size_m
[xmin,ymin,xmax,ymax] = [clamp(v) for v in bbox]




def loadBuildings(bbox):
    buildings = []

    #NL
    bs = loadFeatures('/home/juju/geodata/NL/bu_integrated.gpkg', bbox)
    for bu in bs: formatBuildingNL(bu)
    buildings += bs

    #PL
    bs = loadFeatures('/home/juju/geodata/PL/bdot10k/bu_bubd_bdot10k.gpkg', bbox)
    for bu in bs: formatBuildingPL(bu)
    buildings += bs

    #FR
    bs = loadFeatures('/home/juju/geodata/FR/BD_TOPO/BATI/batiment_3035.gpkg', bbox)
    for bu in bs: formatBuildingFR(bu)
    buildings += bs

    #LU
    bs = loadFeatures('/home/juju/geodata/LU/ACT/BDLTC_SHP/BATI/BATIMENT_3035.gpkg', bbox)
    for bu in bs: formatBuildingLU(bu)
    buildings += bs

    #IT
    bs = loadFeatures('/home/juju/geodata/IT/DBSN/dbsn.gpkg', bbox)
    for bu in bs: formatBuildingIT(bu)
    buildings += bs

    #TODO remove duplicates

    return buildings



#NL
res_NL = ["woonfunctie", "logiesfunctie"]
act_NL = ["overige gebruiksfunctie", "industriefunctie", "kantoorfunctie", "sportfunctie", "winkelfunctie", "gezondheidszorgfunctie", "bijeenkomstfunctie", "onderwijsfunctie", "celfunctie"]
cul_NL = ["windmolen: korenmolen","kerk","kasteel","kapel","bunker","vuurtoren","toren","windmolen: watermolen","windmolen","klooster, abdij","moskee","fort","waterradmolen","paleis","overig religieus gebouw","klokkentoren","koepel","synagoge"]
def formatBuildingNL(bu):

    #construction year
    #y = bu["bouwjaar"]

    #3dbag_b3_height_lod12   height, in m
    h = bu["3dbag_b3_height_lod12"]
    #gebruiksdoel - use
    u = bu["gebruiksdoel"]
    #typegebouw - nature
    t = bu["top10nl_typegebouw"]

    keepOnlyGeometry(bu)

    #buildings heigth
    if(h!=None and (h>250 or h<0)): h=1
    bu["floor_nb"] = 1 if h==None or isnan(h) else max(ceil(h/3), 1)

    #building use
    #count types
    u = [] if u==None else u.split(",")
    nb_res=0; nb_act=0
    for u_ in u:
        if u_ in res_NL: nb_res+=1
        if u_ in act_NL: nb_act+=1
    nb = nb_act + nb_res

    bu["residential"] = 0 if nb==0 else nb_res/nb
    bu["activity"] = 0 if nb==0 else nb_act/nb

    #building cultural nature
    #count types
    t = [] if t==None else t.split("|")
    nb_cul=0; nb=0
    for t_ in t:
        nb+=1
        if t_ in cul_NL: nb_cul+=1
    bu["cultural_value"] = 0 if nb==0 else nb_cul/nb



#PL
def formatBuildingPL(bu):

    #floor number
    u = bu["LKOND"]
    if u==None: u = 1
    #monument
    m = bu["ZABYTEK"]
    #function
    f = bu["FUNOGBUD"]

    keepOnlyGeometry(bu)

    #LKOND - KODKST
    bu["floor_nb"] = int(u)

    #FUNOGBUD - main function
    #FUNSZCZ - detailled function
    bu["residential"] = 1 if f in ["budynkiMieszkalneJednorodzinne","budynkiODwochMieszkaniach","budynkiOTrzechIWiecejMieszkaniach","budynkiZbiorowegoZamieszkania"] else 0
    bu["activity"] = 1 if f in ["budynekGospodarstwaRolnego",
    "budynkiBiurowe",
    "budynkiHandlowoUslugowe",
    "budynkiHoteli",
    "budynkiKulturyFizycznej",
    "budynkiLacznosciDworcowITerminali",
    "budynkiMuzeowIBibliotek",
    "budynkiPrzemyslowe",
    "budynkiSzkolIInstytucjiBadawczych",
    "budynkiSzpitaliIZakladowOpiekiMedycznej",
    "budynkiZakwaterowaniaTurystycznegoPozostale",
    "ogolnodostepneObiektyKulturalne",
    "pozostaleBudynkiNiemieszkalne",
    "zbiornikSilosIBudynkiMagazynowe"] else 0
    bu["cultural_value"] = 1 if m=="Tak" or f in ["budynekZabytkowy","budynkiKultuReligijnego"] else 0


#IT
def formatBuildingIT(bu):
    u = bu["edifc_uso"]
    if u!=None: u = u[:2]

    t = bu["edifc_ty"]
    if t!=None: t = t[:2]

    m = bu["edifc_mon"]
    if m!=None: m = m[:2]

    a = bu["edifc_at"]

    keepOnlyGeometry(bu)

    if a != None and a != -9999 and a!=0 and a!=-29997.0 and a!=-29999.0 : print("Elevation provided for IT building:", a)

    #TODO find information on IT building height
    #bu_top = average_z_coordinate(bu["geometry"])
    #if(bu_top != 0): print("Elevation provided for IT building geometry:", bu_top)
    bu["floor_nb"] = 1

    bu["residential"] = 1 if u=="01" else 0.25 if u=="93" else 0
    bu["activity"] = 1 if u in ["02","03","04","06","07","08","09","10","11","12"] else 0.25 if u=="93" else 0
    bu["cultural_value"] = 1 if u=="05" or m=="01" or t in ["03","06","07","10","11","12","13","15","16","17","18","20","22","24","25"] else 0

#LU
DTM_LU = None
def get_DTM_LU(DTM_LU):
    if DTM_LU==None: DTM_LU = rasterio.open("/home/juju/geodata/LU/MNT_lux2017_3035.tif")
    return DTM_LU
def formatBuildingLU(bu):
    n = bu["NATURE"]
    if n==None: n=0
    n = int(n)
    keepOnlyGeometry(bu)

    #estimate building height from geometry 'z' and DTM
    bu_top = average_z_coordinate(bu["geometry"])
    centroid = bu["geometry"].centroid
    row, col = get_DTM_LU(DTM_LU).index(centroid.x, centroid.y)
    elevation = get_DTM_LU(DTM_LU).read(1, window=((row, row+1), (col, col+1)))[0][0]
    h = bu_top - elevation
    if elevation == -32767 or bu_top > 1000 or bu_top<0 or elevation<0 or elevation>700: h=3
    if h>40*3: h=3 #if a building has more than 40 floors, then there is a bug. Set height to one floor only.

    bu["floor_nb"] = 1 if h==None or isnan(h) else max(ceil(h/3), 1)

    bu["residential"] = 1 if n==0 else 0
    bu["activity"] = 1 if (n>=10000 and n<42000) or n==80000 or n==11000 else 0
    bu["cultural_value"] = 1 if n in [41004,41005,41302,41303,41305] or (n>=50000 and n<=50011) else 0

#FR
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
