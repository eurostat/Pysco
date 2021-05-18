from pyproj import CRS,Transformer
import csv, math

#https://pyproj4.github.io/pyproj/stable/index.html

crsLAEA = CRS.from_epsg(3035)
crsWGS84 = CRS.from_epsg(4326)
t1 = Transformer.from_crs(crsLAEA, crsWGS84)
t2 = Transformer.from_crs(crsWGS84, crsLAEA)

f = open("out.csv", "w")
f.write('POINT_ID","X_LAEA","Y_LAEA","TH_LAT","TH_LONG","ERR1_M","ERR2_M\n')

#file = 'LU_2018_20200213.CSV.csv'
file = "EU_2018_20200213.CSV"
with open(file) as csvfile:
    r = csv.reader(csvfile, delimiter=',')
    for row in r:
        if len(row) < 6 : continue
        id = row[0]
        if id[0:5] == "POINT" : continue
        x = float(id[:4]) * 1000
        y = float(id[4:]) * 1000
        lat = row[5]
        lon = row[6]
        #print(id,x,y,lat,lon)

        tr = t2.transform(lat, lon)
        dx = x-float(tr[1])
        dy = y-float(tr[0])
        err1 = math.sqrt(dx*dx+dy*dy)
        #print(err1)

        tr = t1.transform(y, x)
        tr = t2.transform(tr[0],tr[1])
        dx = x-float(tr[1])
        dy = y-float(tr[0])
        err2 = math.sqrt(dx*dx+dy*dy)
        #print(err2)

        if (err1 > 0.001 or err2 > 0.002 ) : print(id, err1, err2)

        f.write(id+","+str(x)+","+str(y)+","+str(lat)+","+str(lon)+","+str(err1)+","+str(err2)+"\n")

f.close()
