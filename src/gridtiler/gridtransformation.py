import os
import csv
from gridtiler import get_csv_header,round_floats_to_ints

def grid_transformation(
    input_file,
    function,
    output_file
):

    #open file to read
    with open(input_file, 'r') as infile:
        csvreader = csv.DictReader(infile)

        #check output file exists
        file_exists = os.path.exists(output_file)
        with open(output_file, 'w') as outfile:
            writer = None

            #iterate through cells from the input CSV file
            for c in csvreader:

                #apply function
                function(c)
                round_floats_to_ints(c)

                #create writer, if necessary, write file header
                if writer==None:
                    csv_header = get_csv_header(c)
                    writer = csv.DictWriter(outfile, fieldnames=csv_header)
                    if not file_exists: writer.writeheader()

                #write cell data
                writer.writerow(c)
