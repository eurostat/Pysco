import fiona
import geopandas as gpd
from datetime import datetime



bbox1 = (4000000, 2700000, 4100000, 2800000)
bbox2 = [4000000, 2700000, 4100000, 2800000]
gpkg_file = "/home/juju/geodata/FR/BD_TOPO/BATI/batiment_3035.gpkg"

print(datetime.now(), "start")



#fiona loading

#open gpkg file
with fiona.open(gpkg_file, 'r', bbox=bbox1) as gpkg:
    features = list(gpkg.items(bbox=bbox1))
    print(datetime.now(), len(features))

print(datetime.now())




#geopandas loading

features = gpd.read_file('/home/juju/geodata/FR/BD_TOPO/BATI/batiment_3035.gpkg', bbox=bbox2)
print(datetime.now(), len(features))

