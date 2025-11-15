
# get duration in s from speed in kph and distance in meters
kph_to_s = lambda kph,dm: dm / kph * 3.6

'''
FOW
-1 : Not Applicable
1 : Part of Motorway
2 : Part of Multi Carriageway which isNot a Motorway
3 : Part of a Single Carriageway
4 : Part of a Roundabout
6 : Part of an ETA: Parking Place
7 : Part of an ETA: Parking Garage(Building)
8 : Part of an ETA: Unstructured TrafficSquare
10 : Part of a Slip Road
11 : Part of a Service Road
12 : Entrance/Exit to/from a Car Park
14 : Part of a Pedestrian Zone
15 : Part of a Walkway
17 : Special Traffic Figures
18 : Part of an ETA: Gallery
19 : Stairs
20 : Road for Authorities
21 : Connector
22 : Cul-de-Sac
'''

def weight_function(feature, length):
    p = feature['properties']
    fow = p['FOW']

    # ferry case: force 20 kph
    if fow==-1 and p['FEATTYP']==4130:
        w = kph_to_s(20, length)
        return [w,w]

    kph_pos = p['AVERAGE_SPEED_POS']
    kph_neg = p['AVERAGE_SPEED_NEG']

    # case when no av speed is defined: use kph, or very slow value - 10 kph
    if kph_pos == None and kph_neg == None:
        kph = p['KPH']
        # very slow cases, for pedestrian areas
        if fow in [14,15,17,18]: kph = 10
        # stairs
        if fow==19: return [None,None]
        # authorities
        if fow==20: return [None,None]
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
    fow = p['FOW']
    return fow in [1, 10, 20, 21] or p['FREEWAY'] == 1 or (fow==-1 and p['FEATTYP']==4130)


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

# return if the start/end of a section is blocked
def is_start_blocked(f):
    b = f['properties']['F_BP']
    r = b in [1,2,11,12,21,22]
    if r: print(r, b)
    return r
def is_end_blocked(f):
    b = f['properties']['T_BP']
    r = b in [1,2,11,12,21,22]
    if r: print(r, b)
    return r
