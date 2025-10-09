
'''
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
'''

# get duration in s from speed in kph and distance in meters
kph_to_s = lambda kph,dm: dm / kph * 3.6


def weight_function(feature, length):
    p = feature['properties']

    # ferry case: force 20 kph
    if p['fow']==-1 and p['feattyp']==4130:
        w = kph_to_s(20, length)
        return [w,w]

    # private/restricted/pedestrian roads
    #elif p['ONEWAY']=='N': kph = 15
    # default case
     #p['KPH']

    kph_pos = p['average_speed_pos']
    kph_neg = p['average_speed_neg']

    # case when no av speed is defined: use kph, or very slow value - 10 kph
    if kph_pos == None and kph_neg == None:
        kph = p['kph']
        if kph == None or kph<=0: kph = 10
        w = kph_to_s(kph, length)
        return [w,w]

    # compute weights from speed
    w_pos = -1 if kph_pos == None else kph_to_s(kph_pos, length)
    w_neg = -1 if kph_neg == None else kph_to_s(kph_neg, length)
    return [ w_pos, w_neg ]





# return wether a section cannot be used as access point. Residential roads can, highways and ferry lines cannot.
def is_not_snappable_fun(f):
    p = f['properties']
    return p['fow'] in [1,10,12,6] or p['freeway'] == 1 or (p['fow']==-1 and p['feattyp']==4130)


# code to tag the level of the initial node of the section
def initial_node_level_fun(f): return f['properties']['f_elev']
# code to tag the level of the final node of the section
def final_node_level_fun(f): return f['properties']['t_elev']

