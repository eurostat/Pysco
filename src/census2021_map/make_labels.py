import svgwrite
import fiona



path_svg = '/home/juju/gisco/census_2021_map/map_age_labels.svg'
gpkg_path = '/home/juju/gisco/census_2021_map/labels_filtered.gpkg'


# transform for europe view
# A0 dimensions in millimeters (landscape)
scale = 1/5000000
width_mm = 1189
height_mm = 841
cx = 3700000
cy = 3400000
width_m = width_mm / scale / 1000
height_m = height_mm / scale / 1000
x_min, x_max = cx - width_m/2, cx + width_m/2
y_min, y_max = cy - height_m/2, cy + height_m/2
transform_str = f"scale({scale*1000*96/25.4} {scale*1000*96/25.4}) translate({-x_min} {-y_min})"



layer = fiona.open(gpkg_path)

dwg = svgwrite.Drawing(path_svg, size=(f'{width_mm}mm', f'{height_mm}mm'))









print("Load cell data", res)
cells = []
with open(in_CSV, mode='r', newline='') as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        if row['T'] == '0' or row['T'] == '': continue
        del row['M']
        del row['F']
        del row['EMP']
        del row['NAT']
        del row['EU_OTH']
        del row['OTH']
        del row['SAME']
        del row['CHG_IN']
        del row['CHG_OUT']
        del row['NB']
        del row['CONFIDENTIALSTATUS']
        del row['POPULATED']
        del row['LAND_SURFACE']

        row['x'] = int(row['x'])
        row['y'] = int(row['y'])
        row['T'] = int(row['T'])
        cells.append(row)

print(len(cells), "cells loaded")
#print(cells[0])

print("Sort cells")
cells.sort(key=lambda d: (-d['y'], d['x']))



# Create group elements
gCircles = dwg.g(id='circles', transform=transform_str)
gBN = dwg.g(id='boundaries', transform=transform_str, stroke="#777", fill="none", stroke_width=1500, stroke_linecap="round", stroke_linejoin="round")
dwg.add(gBN)
dwg.add(gCircles)

# Set the background color to white
#dwg.add(dwg.rect(insert=(x_min, y_min), size=(width_m, height_m), fill='#dfdfdf'))


print("Draw cells")

for cell in cells:
    t = cell['T']
    t = t / max_pop
    if t>1: t=1
    t = pow(t, power)
    diameter = min_diameter + t * (max_diameter - min_diameter)

    p0 = 0 if cell['Y_LT15']=="" else int(cell['Y_LT15'])
    p1 = 0 if cell['Y_1564']=="" else int(cell['Y_1564'])
    p2 = 0 if cell['Y_GE65']=="" else int(cell['Y_GE65'])
    t = cell['T']
    tot = p0 + p1 + p2

    if tot == 0: color = "gray"
    else:
        #compute shares
        s0, s1, s2 = p0 / tot, p1 / tot, p2 / tot

        #class 0
        if s0 >= c0 and s1 <= c1 and s2 <= c2:
            #central class near class 0
            if cc != None and (s2 - c2) * (c1 - cc * c1) >= (s1 - cc * c1) * (cc * c2 - c2):
                color = centerColor
            else:
                color = col0

        #class 1
        elif s0 <= c0 and s1 >= c1 and s2 <= c2:
            #central class near class 1
            if cc != None and (s2 - c2) * (c0 - cc * c0) >= (s0 - cc * c0) * (cc * c2 - c2):
                color = centerColor
            else:
                color = col1
        
        #class 2
        elif s0 <= c0 and s1 <= c1 and s2 >= c2:
            #central class near class 2
            if cc != None and (s1 - c1) * (c0 - cc * c0) >= (s0 - cc * c0) * (cc * c1 - c1):
                color = centerColor
            else:
                color = col2
        
        #middle class 0 - intersection class 1 and 2
        elif (s0 <= c0 and s1 >= c1 and s2 >= c2):
            #central class
            if cc != None and s0 > cc * c0: color = centerColor
            elif withMixedClasses: color=colm0 #return "m0"
            else: color = col1 if s1>s2 else col2
        
        #middle class 1 - intersection class 0 and 1
        elif (s0 >= c0 and s1 <= c1 and s2 >= c2):
            #central class
            if cc != None and s1 > cc * c1: color = centerColor
            elif withMixedClasses: color=colm1 #return "m1"
            else: color = col0 if s0>s2 else col2
        
        #middle class 2 - intersection class 0 and 1
        elif (s0 >= c0 and s1 >= c1 and s2 <= c2):
            #central class
            if cc != None and s2 > cc * c2: color = centerColor
            elif withMixedClasses: color=colm2 #return "m2"
            else: color = col1 if s1>s0 else col0

        else:
            print("aaa")
            color = "blue"

    #print(color)
    gCircles.add(dwg.circle(center=(round(cell['x']+res/2), round(y_min + y_max - cell['y']+res/2)), r=round(diameter/2), fill=color))

# draw boundaries
lines = fiona.open('/home/juju/gisco/census_2021_map/BN_3M_2021.gpkg') 
for feature in lines:

    if feature['properties'].get("EU_FLAG") != 'T': continue
    if feature['properties'].get("COAS_FLAG") == 'T': continue
    if feature['properties'].get("LEVL_CODE") != 0: continue

    geom = feature.geometry
    for line in geom['coordinates']:
        points = [ (round(x), round(y_min + y_max - y)) for x, y in line]
        gBN.add(dwg.polyline(points))


print("Save SVG", res)
dwg.save()
