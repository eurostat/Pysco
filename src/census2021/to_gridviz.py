from pygridmap import gridtiler
from datetime import datetime


transform = False
aggregation = True

folder = "/home/juju/geodata/census/"
input_file = folder + "csv_export.csv"


def transform_fun(c):
    #fid,GRD_ID,T,M,F,Y_LT15,Y_1564,Y_GE65,EMP,NAT,EU_OTH,OTH,SAME,CHG_IN,CHG_OUT

    #filter out cells with no population
    t = c["T"]
    if t=="0" or t=="": return False

    del c["fid"]

    #get x and y
    a = c['GRD_ID'].split("N")[1].split("E")
    c["x"] = int(a[1])
    c["y"] = int(a[0])
    del c['GRD_ID']

    #remove zeros
    for p in "T","M","F","Y_LT15","Y_1564","Y_GE65","EMP","NAT","EU_OTH","OTH","SAME","CHG_IN","CHG_OUT":
        v = c[p]
        if v == "0": c[p] = ""

#apply transform
if transform: gridtiler.grid_transformation(input_file=input_file, output_file=folder+"out/1000.csv", function=transform_fun)



#aggregation
if aggregation:
    for a in [2,5,10]:
        print(datetime.now(), "aggregation to", a*1000, "m")
        gridtiler.grid_aggregation(input_file=folder+"out/1000.csv", resolution=1000, output_file=folder+"out/"+str(a*1000)+".csv", a=a)
    for a in [2,5,10]:
        print(datetime.now(), "aggregation to", a*10000, "m")
        gridtiler.grid_aggregation(input_file=folder+"out/10000.csv", resolution=10000, output_file=folder+"out/"+str(a*10000)+".csv", a=a)

