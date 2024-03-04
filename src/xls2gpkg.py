import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

# transform xls segments into GPKG file
def xlsToGPKG(inXLSfile, lon1, lat1, lon2, lat2, id, outGPKGFile):

    print("Load data from "+inXLSfile)
    df = pd.read_excel(inXLSfile)
    print(str(len(df)) + " segments loaded")

    print("Make features")
    geometries = []
    for index, row in df.iterrows():
        try:
            geometries.append(LineString([(row[lon1], row[lat1]), (row[lon2], row[lat2])]))
        except Exception as e:
            print("Problem with segment "+row[id]+":", e)
            geometries.append(LineString([]))

    print("Save as GPKG file")
    gdf = gpd.GeoDataFrame(df, geometry=geometries)
    gdf.to_file(outGPKGFile, driver='GPKG', crs="EPSG:4258")


folder = "/home/juju/Bureau/gisco/rail_rinf/"
# folder = ".\\"

# transform annex G
xlsToGPKG(folder+"NET_SEGMENTS_EU_EFTA.xlsx", 'Fromlongitude', 'Fromlatitude', 'Tolongitude', 'Tolatitude', "Network segment identifier", folder+'out.gpkg')
# transform RINF
xlsToGPKG(folder+"RINF_EU_EFTA.xlsx", 'Point Start Longitude', 'Point Start Latitude', 'Point End Longitude', 'Point End Latitude', "ID", folder+'out_rinf.gpkg')
