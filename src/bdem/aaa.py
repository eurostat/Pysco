import fiona

gpkg_file = "/home/juju/geodata/NL/BAG/baglight__pand.gpkg"



with fiona.open(gpkg_file) as layer:
    for feature in layer:
        u = feature['properties'].get('gebruiksdoel')
        u = u.split(",")
        print(len(u))
