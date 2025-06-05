

# driving direction
def direction_fun(feature):
    d = feature['properties']['ONEWAY']
    if d==None or d=="": return 'both'
    if d=="FT": return 'forward'
    if d=="TF": return 'backward'
    if d=="N": return 'both'
    print("Unexpected driving direction: ", d)
    return None

def weight_function(feature, length):
    p = feature['properties']
    kph = 0
    # ferry
    if p['FOW']==-1 and p['FEATTYP']==4130: kph = 30
    # private/restricted/pedestrian roads
    elif p['ONEWAY']=='N': kph = 15
    # default case
    else: kph = p['KPH']
    if kph==0: return -1
    # duration in seconds
    return 1.1 * length / kph * 3.6
def is_not_snappable_fun(f):
    p = f['properties']
    return p['FOW'] in [1,10,12,6] or p['FREEWAY'] == 1 or (p['FOW']==-1 and p['FEATTYP']==4130)
def initial_node_level_fun(f): return f['properties']['F_ELEV']
def final_node_level_fun(f): return f['properties']['T_ELEV']
