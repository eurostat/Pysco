import geopandas as gpd
from shapely.errors import GEOSException
from datetime import datetime
import math
from netutils import shortest_path_geometry,graph_from_geodataframe,nodes_spatial_index,a_star_euclidian_dist
from ome2utils import ome2_filter_road_links
import networkx as nx

folder = '/home/juju/Bureau/gisco/OME2_analysis/'
file_path = '/home/juju/Bureau/gisco/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg'
distance_threshold = 3000

def validation(cnt1,cnt2):

    print(datetime.now(), "load nodes to get boundaries")
    nodes = gpd.read_file(folder+"xborder_nodes_stamped.gpkg")
    #print(str(len(nodes)) + " nodes")

    print(datetime.now(), "select for "+cnt1+" and "+cnt2+" only")
    condition = (nodes['country_id'] == cnt1) | (nodes['country_id'] == cnt2)
    nodes = nodes[condition]
    #print(len(nodes), " selected nodes")

    #get bbox and partition information
    window = 30000
    bbox = nodes.total_bounds
    rnd_function = lambda x: int(window*math.ceil(x/window))
    bbox = [rnd_function(x) for x in bbox]
    [xmin, ymin, xmax, ymax] = bbox
    nbx = int((xmax-xmin)/window)
    nby = int((ymax-ymin)/window)
    #print(nbx, nby, bbox)
    window_margin = window * 0.1

    #output paths
    sp_geometries = []

    #iterate through partition
    for i in range(nbx):
        for j in range(nby):
            bbox = [xmin+i*window-window_margin, ymin+j*window-window_margin, xmin+(i+1)*window+window_margin, ymin+(j+1)*window+ window_margin]
            print("******" ,bbox)

            print(datetime.now(), "load nodes")
            nodes = gpd.read_file(folder+"xborder_nodes_stamped.gpkg", bbox=bbox)
            #print(len(nodes))
            if(len(nodes)==0): continue

            #filter nodes per country
            nodes1 = nodes[nodes['country_id'] == cnt1]
            nodes2 = nodes[nodes['country_id'] == cnt2]
            del nodes
            #print(len(nodes1), len(nodes2))
            if(len(nodes1)==0): continue
            if(len(nodes2)==0): continue

            print(datetime.now(), "load network links")
            rn = gpd.read_file(file_path, layer='tn_road_link', bbox=bbox)
            #print(len(rn))
            if(len(rn)==0): continue

            print(datetime.now(), "filter network links")
            rn = ome2_filter_road_links(rn)
            #print(len(rn))
            if(len(rn)==0): continue

            print(datetime.now(), "make graph")
            graph = graph_from_geodataframe(rn, lambda f:f.geometry.length)
            del rn

            print(datetime.now(), "make list of nodes")
            nodes_ = []
            for node in graph.nodes(): nodes_.append(node)

            print(datetime.now(), "make nodes spatial index")
            idx = nodes_spatial_index(graph)

            print(datetime.now(), "compute paths")
            for iii,n1 in nodes1.iterrows():
                #get country 1 node
                n1_ = nodes_[next(idx.nearest((n1.geometry.x, n1.geometry.y, n1.geometry.x, n1.geometry.y), 1))]
                for jjj,n2 in nodes2.iterrows():

                    #skip node pairs too far away
                    d = n1.geometry.distance(n2.geometry)
                    if(d > distance_threshold): continue

                    #get country 2 node
                    n2_ = nodes_[next(idx.nearest((n2.geometry.x, n2.geometry.y, n2.geometry.x, n2.geometry.y), 1))]

                    #may happen (?)
                    if(n1_==n2_): continue

                    try:
                        #compute shortest path
                        sp = nx.astar_path(graph, n1_, n2_, heuristic=a_star_euclidian_dist, weight="weight")
                        line = shortest_path_geometry(sp)
                        sp_geometries.append(line)
                    except nx.NetworkXNoPath as e: pass#print("Exception NetworkXNoPath:", e)
                    except GEOSException as e: print("Exception GEOSException:", e)

            print(datetime.now(), len(sp_geometries), "paths")


    if(len(sp_geometries)==0): exit()

    print(datetime.now(), "export paths as geopackage", len(sp_geometries))
    gdf = gpd.GeoDataFrame({'geometry': sp_geometries})
    gdf.crs = 'EPSG:3035'
    gdf.to_file(folder+"ome2_validation_paths"+cnt1+"_"+cnt2+".gpkg", driver="GPKG")

validation("be", "fr")
validation("be", "nl")
