import csv
import fiona
from fiona.crs import CRS
from shapely.geometry import Polygon,box,shape,mapping


def csv_grid_to_geopackage(csv_grid_path, gpkg_grid_path, geom="surf"):

    #load csv
    data = None
    with open(csv_grid_path, mode="r", newline="") as file:
        reader = csv.DictReader(file)
        data = list(reader)

    cells = []
    for p in data:
        #make cell
        c = {"type":"Feature", "properties":p}

        #grid_id to x,y
        a = p['GRD_ID'].split("N")[1].split("E")
        x = int(a[1])
        y = int(a[0])

        #make grid cell geometry
        grid_resolution = 1000
        cell_geometry = Polygon([(x, y), (x+grid_resolution, y), (x+grid_resolution, y+grid_resolution), (x, y+grid_resolution)])
        c["geometry"] = mapping(cell_geometry)

        cells.append(c)

    schema = get_schema_from_feature(cells[0])
    out = fiona.open(gpkg_grid_path, 'w', driver='GPKG', crs=CRS.from_epsg(3035), schema=schema)
    out.writerecords(cells)

