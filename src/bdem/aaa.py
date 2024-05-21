import fiona

gpkg_file = "/home/juju/geodata/NL/BAG/baglight__pand.gpkg"


ddd = []
with fiona.open(gpkg_file) as layer:
    for feature in layer:
        u = str(feature['properties'].get('gebruiksdoel'))
        u = u.split(",")
        #nb = len(u)
        #if nb>1: print(nb, u)
        for u_ in u:
            if u_ in ddd: continue
            print(u_)
            ddd.append(u_)

print(ddd)
