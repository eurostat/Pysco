from pygridmap import gridtiler


folder = "/home/juju/geodata/census/"
input_file = folder + "csv_export.csv"


def transform(c):
    #fid,GRD_ID,T,M,F,Y_LT15,Y_1564,Y_GE65,EMP,NAT,EU_OTH,OTH,SAME,CHG_IN,CHG_OUT
    del c["fid"]

    id = c["GRD_ID"]
    c["x"] = 0
    c["y"] = 0
    del c["GRD_ID"]

    for p in "T","M","F","Y_LT15","Y_1564","Y_GE65","EMP","NAT","EU_OTH","OTH","SAME","CHG_IN","CHG_OUT":
        v = c[p]
        if v == "0": c[p] = ""



gridtiler.grid_transformation(input_file=input_file, output_file=folder+"out/1.csv", function=transform)

