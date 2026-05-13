import csv
from utils.gridutils import grid_to_geopackage


input_path = "/home/juju/geodata/census/2021/input20250123/"
output_path = "/home/juju/gisco/census_2021_production/"


'''
DATAFLOW,FREQ,
STAT,
SPATIAL,TIME_PERIOD,
OBS_VALUE,
NOT_COUNTED_PROPORTION,GENERAL_STATUS,
OBS_STATUS,STATUS,
LAND_SURFACE,
SPECIAL_VALUE,APPROXIMATELY_LOCATED_POPULATION_PROPORTION,OBS_NOTE,MEASURE,
MEASUREMENT_METHOD,UNIT_MEASURE,
CONVENTIONALLY_LOCATED_PROPORTION,UNIVERSE,POPULATED,
AREA_OF_DISSEMINATION,INSPIREID

ESTAT:DF_CENSUS_GRID_2021(2.0),A10,
T,
LU_CRS3035RES1000mN2975000E4014000,2021,
0,
0,final,
,final,
0,
,0,,
populationAtResidencePlace,count,
PS,0,,0,
LU,



ESTAT:DF_CENSUS_GRID_2021(2.0),A10,
CHG_IN,
LU_CRS3035RES1000mN2977000E4014000,2021,
,
0,final,
,final,
0.0935,
confidential,0,,
populationAtResidencePlace,count,
PS,0,,1,
LU,



stat indic: STAT
grid cell: SPATIAL
value: OBS_VALUE
confidential: SPECIAL_VALUE
'''



# output cells, as dict indexed by cell_id
cells = {}

for cc in ["LU", "BE"]:
    csv_path = input_path + f"CENSUS_GRID_N_{cc}_2021.csv"

    with open(csv_path) as f: #, newline="", encoding="utf-8"
        rows = list(csv.DictReader(f))
        for row in rows:

            # get cell id
            id = row["SPATIAL"][3:]

            # get cell
            cell = cells.get(id)

            # no cell: create one
            if cell is None:
                cell = { "id": id, "cnt": [cc] }
                cells[id] = cell

            # coutnry code
            cnt = cell["cnt"]
            if cc not in cnt: cnt.append(cc)

            # set cell value
            #stat = row["STAT"]
            #stat_ci = row["SPECIAL_VALUE"]
            #cell[stat] = row["OBS_VALUE"]


# cells dict to values list
cells = list(cells.values())

for cell in cells:
    # sort country codes in cell
    cell["cnt"] = ",".join(sorted(cell["cnt"]))


# save cells as geopackage
grid_to_geopackage(cells, output_path + "census_grid_2021.gpkg")

