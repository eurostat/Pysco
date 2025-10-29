

# get duration in s from speed in kph and distance in meters
kph_to_s = lambda kph,dm: dm / kph * 3.6


def weight_function(feature, length):
    p = feature['properties']

    # ferry case: force 20 kph
    if p['FOW']==-1 and p['FEATTYP']==4130:
        w = kph_to_s(20, length)
        return [w,w]

    # private/restricted/pedestrian roads
    #elif p['ONEWAY']=='N': kph = 15
    # default case
     #p['KPH']

    kph_pos = p['AVERAGE_SPEED_POS']
    kph_neg = p['AVERAGE_SPEED_NEG']

    # case when no av speed is defined: use kph, or very slow value - 10 kph
    if kph_pos == None and kph_neg == None:
        kph = p['KPH']
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
    return p['FOW'] in [1,10,12,6] or p['FREEWAY'] == 1 or (p['FOW']==-1 and p['FEATTYP']==4130)


# code to tag the level of the initial node of the section
def initial_node_level_fun(f): return f['properties']['F_ELEV']
# code to tag the level of the final node of the section
def final_node_level_fun(f): return f['properties']['T_ELEV']


'''
F_BP - From blocked passage
T_BP - To blocked passage
1 : Blocked at Start Junction, notRemovable
2 : Blocked at End Junction, notRemovable
11 : Accessible for EmergencyVehicles at Start
12 : Keyed Access at Start
13 : Guard Controlled at Start
21 : Accessible for EmergencyVehicles at End
22 : Keyed Access at End
23 : Guard Controlled at End
'''




