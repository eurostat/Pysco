

# driving direction
def direction_fun(feature):
    d = feature['properties']['ONEWAY']
    if d==None or d=="": return 'both'
    if d=="FT": return 'forward'
    if d=="TF": return 'backward'
    if d=="N": return 'both'
    print("Unexpected driving direction:", d)
    return None


# the weight of a length of a road, for routing. This is the estimated driving time.
def weight_function(feature, length):
    p = feature['properties']
    kph = 0

    # ferry
    if p['FOW']==-1 and p['FEATTYP']==4130: kph = 30
    # private/restricted/pedestrian roads
    elif p['ONEWAY']=='N': kph = 15
    # default case
    else: kph = p['KPH']

    # non drivable case
    if kph == 0: return -1

    # duration in seconds, rounded, based on the speed. Plus 10% assuming kph is the maximum speed with no traffic and no stops.
    # 1.1 * 
    return 1.1 * round(length / kph * 3.6)



def weight_function_positive(feature, length):
    return 0

def weight_function_negative(feature, length):
    return 0



# return wether a section cannot be used as access point. Residential roads can, highways and ferry lines cannot.
def is_not_snappable_fun(f):
    p = f['properties']
    return p['FOW'] in [1,10,12,6] or p['FREEWAY'] == 1 or (p['FOW']==-1 and p['FEATTYP']==4130)


# code to tag the level of the initial node of the section
def initial_node_level_fun(f): return f['properties']['F_ELEV']
# code to tag the level of the final node of the section
def final_node_level_fun(f): return f['properties']['T_ELEV']

