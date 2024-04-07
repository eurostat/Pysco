import geopandas as gpd
from shapely.geometry import LineString
from datetime import datetime
import matplotlib.pyplot as plt

folder = '/home/juju/Bureau/gisco/OME2_analysis/'
buffer_distance = 5000

print(datetime.now(), "load boundaries")
gdf = gpd.read_file(folder+"bnd_3km.gpkg")
print(str(len(gdf)) + " boundaries")


fig, ax = plt.subplots()
gdf.plot(ax=ax, color='blue', edgecolor='black')

for i, f in gdf.iterrows():
    buffered_geometry = f.geometry.buffer(buffer_distance)

    for polygon in buffered_geometry:
        ax.add_patch(plt.Polygon(polygon.exterior, color='green', alpha=0.5))

ax.set_title('Buffer Visualization')
plt.show()
