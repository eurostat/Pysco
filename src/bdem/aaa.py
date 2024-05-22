import fiona

#gpkg_file = "/home/juju/geodata/NL/BAG/baglight__pand.gpkg"
gpkg_file = "/home/juju/geodata/NL/top10nl_Compleet.gpkg"


ddd = []
with fiona.open(gpkg_file, layer="top10nl_gebouw_vlak") as layer:
    for feature in layer:
        u = str(feature['properties'].get('gebruiksdoel'))
        u = u.split("|") # , |
        #nb = len(u)
        #if nb>1: print(nb, u)
        for u_ in u:
            if u_ in ddd: continue
            print(u_)
            ddd.append(u_)

print(ddd)




'''''
gebruiksdoel




typegebouw

overig
kas, warenhuis
tank
school
huizenblok
C windmolen: korenmolen
C kerk
manege
werf
gemeentehuis
C kasteel
C kapel
sporthal
gemaal
politiebureau
pompstation
zwembad
transformatorstation
reddingboothuisje
radiotoren, televisietoren
ruïne
elektriciteitscentrale
kliniek, inrichting, sanatorium
stationsgebouw
postkantoor
psychiatrisch ziekenhuis, psychiatrisch centrum
C bunker
parkeerdak, parkeerdek, parkeergarage
koeltoren
C vuurtoren
crematorium
veiling
watertoren
brandweerkazerne
C toren
universiteit
bezoekerscentrum
kunstijsbaan
silo
uitzichttoren
windmolen: watermolen
radarpost
kerncentrale, kernreactor
museum
lichttoren
radartoren
dok
C windmolen
schoorsteen
remise
schaapskooi
stadion
verkeerstoren
C klooster, abdij
C moskee
C fort
C waterradmolen
telecommunicatietoren
C paleis
gevangenis
C overig religieus gebouw
observatorium
C klokkentoren
C koepel
ziekenhuis
stadskantoor, hulpsecretarie
luchtwachttoren
tankstation
hotel
C synagoge
windturbine
tol
fabriek
'''