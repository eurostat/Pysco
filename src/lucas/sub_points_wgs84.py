from pyproj import CRS,Transformer
import csv, math

#https://pyproj4.github.io/pyproj/stable/index.html

crsLAEA = CRS.from_epsg(3035)
crsWGS84 = CRS.from_epsg(4326)
t = Transformer.from_crs(crsLAEA, crsWGS84)

f = open("sub_points.csv", "w")
f.write('POINT_ID,SUB_CODE,X_LAEA,Y_LAEA,TH_LAT,TH_LONG\n')

subs = [
    {"code":"A1", "dx":-40, "dy":40},
    {"code":"A3", "dx":-40, "dy":20},
    {"code":"A5", "dx":-40, "dy":0},
    {"code":"A7", "dx":-40, "dy":-20},
    {"code":"A9", "dx":-40, "dy":-40},

    {"code":"B2", "dx":-30, "dy":30},
    {"code":"B4", "dx":-30, "dy":10},
    {"code":"B6", "dx":-30, "dy":-10},
    {"code":"B8", "dx":-30, "dy":-30},

    {"code":"C1", "dx":-20, "dy":40},
    {"code":"C3", "dx":-20, "dy":20},
    {"code":"C5", "dx":-20, "dy":0},
    {"code":"C7", "dx":-20, "dy":-20},
    {"code":"C9", "dx":-20, "dy":-40},

    {"code":"D2", "dx":-10, "dy":30},
    {"code":"D4", "dx":-10, "dy":10},
    {"code":"D6", "dx":-10, "dy":-10},
    {"code":"D8", "dx":-10, "dy":-30},

    {"code":"E1", "dx":0, "dy":40},
    {"code":"E3", "dx":0, "dy":20},
    {"code":"E5", "dx":0, "dy":0},
    {"code":"E7", "dx":0, "dy":-20},
    {"code":"E9", "dx":0, "dy":-40},

    {"code":"F2", "dx":10, "dy":30},
    {"code":"F4", "dx":10, "dy":10},
    {"code":"F6", "dx":10, "dy":-10},
    {"code":"F8", "dx":10, "dy":-30},

    {"code":"G1", "dx":20, "dy":40},
    {"code":"G3", "dx":20, "dy":20},
    {"code":"G5", "dx":20, "dy":0},
    {"code":"G7", "dx":20, "dy":-20},
    {"code":"G9", "dx":20, "dy":-40},

    {"code":"H2", "dx":30, "dy":30},
    {"code":"H4", "dx":30, "dy":10},
    {"code":"H6", "dx":30, "dy":-10},
    {"code":"H8", "dx":30, "dy":-30},

    {"code":"I1", "dx":40, "dy":40},
    {"code":"I3", "dx":40, "dy":20},
    {"code":"I5", "dx":40, "dy":0},
    {"code":"I7", "dx":40, "dy":-20},
    {"code":"I9", "dx":40, "dy":-40},

]


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

        for sub in subs:
            x_ = x+sub["dx"]
            y_ = y+sub["dy"]
            tr = t.transform(y_, x_)
            lat = tr[0]
            lon = tr[1]
            #print(x_,y_)
            #print(lat,lon)
            f.write(id+","+sub["code"]+","+str(int(x_))+","+str(int(y_))+","+str(lat)+","+str(lon)+"\n")

f.close()
