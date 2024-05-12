import fiona

# Path to the GeoPackage file
gpkg_file = '/home/juju/gisco/building_demography/out_partition/eurobudem_100m_4000000_2500000.gpkg'

with fiona.open(gpkg_file, 'r') as src:
    for feature in src:
        number = feature['properties']['number']
        if number<=0: continue
        print(number)
        #print("geom:", geometry)
        #print("props:", properties)

