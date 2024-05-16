import os
import csv
from math import floor,pow

def grid_aggregation(
    input_file,
    resolution,
    output_file,
    a,
    aggregation_rounding = 6
):

    # the aggregated cells, indexed by xa and then ya
    aggregation_index = {}
    target_resolution = a*resolution
    keys = None

    print("aggregation indexing...")
    with open(input_file, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)

        #iterate through cells from the input CSV file
        for c in csvreader:
            #get aggregated cell x,y
            xa = target_resolution * floor(float(c["x"]) / target_resolution)
            ya = target_resolution * floor(float(c["y"]) / target_resolution)

            #release memory
            del c["x"]; del c["y"]

            #store keys
            if keys==None: keys = list(c.keys())

            #add cell to its aggregation level
            try: cA_ = aggregation_index[str(xa)]
            except:
                cA_ = {}
                aggregation_index[str(xa)] = cA_
            try: cA = cA_[str(ya)]
            except:
                cA = []
                cA_[str(ya)] = cA
            cA.append(c)

    print("aggregation computation...")

    #aggregation function
    #TODO handle other cases: average, mode, etc
    aggregation_fun = sum

    #prepare function to round aggregated figures
    tolerance = pow(10, aggregation_rounding)
    round_to_tolerance = lambda number : round(number * tolerance) / tolerance

    #aggregate cell values
    for xa, d in aggregation_index.items():
        for ya, cells in d.items():

            #print(xa,ya,len(cells))

            #make aggregated cell
            cA = { "x": xa, "y": ya }

            #compute aggregates values
            for k in keys:
                #get list of values to aggregate
                values = []
                for c in cells: values.append(c[k])
                #compute and set aggregated value
                cA[k] = aggregation_fun(values)
                if (aggregation_rounding != None): cA[k] = round_to_tolerance(cA[k])

            print(cA)

            #TODO write in file

            #release memory immediatelly
            #del d[ya]
