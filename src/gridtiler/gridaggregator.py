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

    with open(input_file, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)

        #iterate through cells from the input CSV file
        for c in csvreader:
            if keys==None: keys = list(c.keys())

            #get aggregated cell x,y
            xa = target_resolution * floor(float(c["x"]) / target_resolution)
            ya = target_resolution * floor(float(c["y"]) / target_resolution)

            #add cell to its aggregation level
            cA_ = aggregation_index[xa]
            if cA_==None:
                cA_ = {}
                aggregation_index[xa] = cA_
            cA = cA_[ya]
            if cA==None: 
                cA = []
                cA_[ya] = cA
            cA.append(c)

    #aggregation function
    #TODO handle other cases: average, mode, etc
    aggregation_fun = sum

    #prepare function to round aggregated figures
    tolerance = pow(10, aggregation_rounding)
    roundToTolerance = lambda number : round(number * tolerance) / tolerance

    #aggregate cell values
    for xa, d in aggregation_index.items():
        for ya, cells in d.items():

            print(xa,ya,len(cells))

            #TODO compute aggregated values
            #TODO write in file

            #release memory immediatelly
            del d[ya]

            """
            //compute aggregates values
            for (let k of keys) {
                //get list of values to aggregate
                const vs = []
                for (let c of cA.cells) vs.push(c[k])
                //compute and set aggregated value
                cA[k] = aggregateSum(vs)
                if (opts.aggregationRounding != undefined)
                    cA[k] = roundToTolerance(cA[k])
            }
            """    
