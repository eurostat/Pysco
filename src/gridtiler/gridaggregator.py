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

    with open(input_file, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)

        #iterate through cells from the input CSV file
        for c in csvreader:

            #get aggregated cell x,y
            xa = target_resolution * floor(c["x"] / target_resolution)
            ya = target_resolution * floor(c["y"] / target_resolution)

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
