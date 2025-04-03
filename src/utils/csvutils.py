import csv

def save_as_csv(csv_filename, data):
    with open(csv_filename, mode="w", newline="") as file:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
