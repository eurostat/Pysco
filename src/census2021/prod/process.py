import csv



input_path = "/home/juju/geodata/census/2021/input20250123/"


for cc in ["LU", "LI"]:
    csv_path = input_path + f"CENSUS_GRID_N_{cc}_2021.csv"

    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        for row in rows:
            print(row)


