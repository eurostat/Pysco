import csv

def save_as_csv(csv_filename, dictionaries_array):
    with open(csv_filename, mode="w", newline="") as file:
        fieldnames = dictionaries_array[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dictionaries_array)
