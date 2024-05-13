import fiona
from datetime import datetime


gpkg_file = "/home/juju/geodata/FR/BD_TOPO/BATI/batiment_3035.gpkg"

print(datetime.now())

#open gpkg file
features = []
with fiona.open(gpkg_file, 'r') as src:
    for feature in src: features.append(feature)


print(datetime.now())

del features

print(datetime.now())
