import csv
from math import floor,pow
from gridtiler import get_csv_header,round_floats_to_ints

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
    with open(input_file, 'r') as infile:
        csvreader = csv.DictReader(infile)

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
    def aggregation_fun(values):
        sum = 0
        for value in values: sum += float(value)
        return sum

    #prepare function to round aggregated figures
    tolerance = pow(10, aggregation_rounding)
    round_to_tolerance = lambda number : round(number * tolerance) / tolerance


    writer = None
    with open(output_file, 'w') as outfile:

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

                #if not, create writer and write header
                if writer == None:
                    writer = csv.DictWriter(outfile, fieldnames=get_csv_header(cA))
                    writer.writeheader()

                #round floats
                round_floats_to_ints(cA)

                #write aggregated cell data in output file
                writer.writerow(cA)

                #TODO release memory immediatelly
                cells.clear()
                #del d[ya]
