import math
import geopandas as gpd
from shapely.geometry import Point,LineString
from shapely.errors import GEOSException
import networkx as nx
from rtree import index
from datetime import datetime

import sys
sys.path.append('/home/juju/workspace/pyEx/src/')

from lib.netutils import shortest_path_geometry,node_coordinate,graph_from_geodataframe,a_star_euclidian_dist,a_star_speed

out_folder = '/home/juju/gisco/OME2_analysis/'

print(datetime.now(), "loading")
xMin = 3900000
yMin = 3000000 
size = 60000
resolution = 1000
gdf = gpd.read_file(out_folder+"test_"+str(size)+"_prepared.gpkg")
print(str(len(gdf)) + " links")
#print(gdf.dtypes)

print(datetime.now(), "make graph")
graph = graph_from_geodataframe(gdf, lambda f:f.duration)
#clear memory
del gdf

print(datetime.now(), "make list of nodes")
nodes = []
for node in graph.nodes(): nodes.append(node)

print(datetime.now(), "make spatial index")
idx = index.Index()
for i in range(graph.number_of_nodes()):
    node = nodes[i]
    [x,y] = node_coordinate(node)
    idx.insert(i, (x,y,x,y))

print(datetime.now(), "compute shortest paths")

#origin node: center
node1 = nodes[next(idx.nearest((xMin+size/2, yMin+size/2, xMin+size/2, yMin+size/2), 1))]

nb = math.ceil(size/resolution)
sp_geometries = []; sp_durations = []
pt_geometries = []; pt_durations = []; pt_resolutions = []
seg_geometries = []; seg_lengths = []

#A* stuff
astar_heuristic_speed_kmh = 50
astar_heuristic = a_star_speed(a_star_euclidian_dist, astar_heuristic_speed_kmh)
astar_cutoff_function = lambda node1, node: 1.5 * a_star_euclidian_dist(node1, node)

for i in range(nb+1):
    for j in range(nb+1):
        x = xMin + i*resolution
        y = yMin + j*resolution
        node = idx.nearest((x, y, x, y), 1)
        node = next(node)
        node = nodes[node]

        #compute distance to network node
        [xN,yN]=node_coordinate(node)
        segg = LineString([(x, y), (xN, yN)])
        distNetw = segg.length

        #point information
        pt_geometries.append(Point(x,y))
        pt_resolutions.append(resolution)
        ptdur = math.inf

        #network segment information
        seg_geometries.append(segg)
        seg_lengths.append(distNetw)
        try:

            #default
            #sp = nx.shortest_path(graph, node1, node, weight="weight")
            #8 min

            #A*
            #https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.astar.astar_path.html
            sp = nx.astar_path(graph, node1, node, heuristic=astar_heuristic, weight="weight") #, cutoff=astar_cutoff_function(node1, node))
            #without cutoff: 1.7 mins
            #with cutoff 2: 1.8 mins
            #with cutoff 1.5: 1.8 mins

            line = shortest_path_geometry(sp)
            sp_geometries.append(line)
            #wt = nx.shortest_path_length(graph, node1, node, weight="weight")
            wt = nx.path_weight(graph, sp, weight='weight')
            sp_durations.append(wt)
            ptdur = wt
        except nx.NetworkXNoPath as e:
            print("Exception NetworkXNoPath:", e)
        except GEOSException as e:
            print("Exception GEOSException:", e)
        pt_durations.append(ptdur)

print(datetime.now(), "export paths as geopackage", len(sp_geometries))
fs = {'geometry': sp_geometries, 'duration': sp_durations}
gdf = gpd.GeoDataFrame(fs)
gdf.crs = 'EPSG:3035'
gdf.to_file(out_folder+"sp.gpkg", driver="GPKG")

print(datetime.now(), "export points as geopackage", len(pt_geometries))
fs = {'geometry': pt_geometries, 'duration': pt_durations, 'resolution': pt_resolutions, 'netdist': seg_lengths}
gdf = gpd.GeoDataFrame(fs)
gdf.crs = 'EPSG:3035'
gdf.to_file(out_folder+"pt.gpkg", driver="GPKG")

print(datetime.now(), "export network segments as geopackage", len(seg_geometries))
fs = {'geometry': seg_geometries, 'dist': seg_lengths}
gdf = gpd.GeoDataFrame(fs)
gdf.crs = 'EPSG:3035'
gdf.to_file(out_folder+"seg.gpkg", driver="GPKG")
