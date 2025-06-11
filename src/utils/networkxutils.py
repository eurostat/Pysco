import networkx as nx

from utils.netutils import distance




def adjacency_dict_to_networkx(graph):
    """
    Converts a directed graph stored as an adjacency dictionary
    into a networkx.DiGraph.

    Parameters:
    - adj_dict (dict): {node: [(destination_node, weight), ...], ...}

    Returns:
    - networkx.DiGraph
    """
    G = nx.DiGraph()

    for node1, edge in graph.items():
        for n2, weight in edge: G.add_edge(node1, n2, weight=weight)
    return G




# make networkx graph from linear features
def graph_from_geodataframe(gdf, weight = lambda feature:feature.geometry.length, coord_simp=round, edge_fun = None, detailled=False):
    graph = nx.Graph()
    for i, feature in gdf.iterrows():
        g = feature.geometry

        if(detailled):
            #make one edge for each segment of the geometry

            #create initial node
            pi = g.coords[0]
            ni = str(coord_simp(pi[0])) +'_'+ str(coord_simp(pi[1]))

            #create graph edge for each line segment
            for i in range(1, len(g.coords)):

                #create final node
                pf = g.coords[i]
                nf = str(coord_simp(pf[0])) +'_'+ str(coord_simp(pf[1]))

                if(ni!=nf):
                    #nodes are different: make edge

                    #compute weight
                    #segment_length = math.hypot(pi[0]-pf[0],pi[1]-pf[1])
                    segment_length = distance(ni,nf) #TODO be more efficient here
                    w = weight(feature, segment_length)
                    if(w<0): continue

                    #add edge
                    graph.add_edge(ni, nf, weight=w)

                    #in case there is a need to do some stuff on the newly created edge, such as copying feature data, etc.
                    if edge_fun != None: edge_fun(graph[pi][pf],feature)

                #initial point becomes final point of the next segment
                pi=pf
                ni=nf

        else:
            #make one single edge, from initial to final vertice of the geometry

            #create initial node
            pi = g.coords[0]
            pi = str(coord_simp(pi[0])) +'_'+ str(coord_simp(pi[1]))

            #create final node
            pf = g.coords[-1]
            pf = str(coord_simp(pf[0])) +'_'+ str(coord_simp(pf[1]))

            #TODO check both nodes are not the same ?

            #compute weight
            w = weight(feature, g.length)
            if(w<0): continue

            #add edge
            graph.add_edge(pi, pf, weight=w)

            #in case there is a need to do some stuff on the newly created edge, such as copying feature data, etc.
            if edge_fun != None: edge_fun(graph[pi][pf],feature)

    return graph
