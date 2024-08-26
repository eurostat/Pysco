import svgwrite
import csv
#import cairosvg


path_svg = '/home/juju/Bureau/map.svg'
path_pdf = '/home/juju/Bureau/map.pdf'
res = 2000
in_CSV = '/home/juju/geodata/census/out/ESTAT_Census_2021_V2_'+str(res)+'.csv'

max_pop = res * 100

# A0 dimensions in millimeters (landscape)
width_mm = 1189
height_mm = 841

# Custom coordinate system extents
cx = 3700000
cy = 3400000
scale = 1/5000000
width_m = width_mm / 1000 / scale
height_m = height_mm / 1000 / scale
x_min, x_max = cx - width_m/2, cx + width_m/2
y_min, y_max = cy - height_m/2, cy + height_m/2


min_diameter = 0.1 / 1000 / scale
max_diameter = res * 1.6
#print(min_diameter, max_diameter)

col0, col1, col2 = "#4daf4a", "#377eb8", "#e41a1c"
c0, c1, c2 = 0.15, 0.6, 0.25
centerColor = "#999"
centerCoefficient = 0.7
cc = centerCoefficient
withMixedClasses = True



def average_color(color1, color2):
    # Convert hex color to RGB tuple
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    # Convert RGB tuple to hex color
    def rgb_to_hex(rgb_tuple):
        return '#{:02x}{:02x}{:02x}'.format(*rgb_tuple)
    
    # Get RGB values from hex colors
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)

    # Calculate the average of each RGB component
    avg_rgb = tuple((c1 + c2) // 2 for c1, c2 in zip(rgb1, rgb2))

    # Convert the averaged RGB values back to a hex color
    return rgb_to_hex(avg_rgb)




# Create an SVG drawing object with A0 dimensions in landscape orientation
dwg = svgwrite.Drawing(path_svg, size=(f'{width_mm}mm', f'{height_mm}mm'))

# Set the viewBox attribute to map the custom coordinates to the SVG canvas
dwg.viewbox(x_min, y_min, width_m, height_m)

# Set the background color to white
#dwg.add(dwg.rect(insert=(x_min, y_min), size=(width_m, height_m), fill='#dfdfdf'))

'''
# Coordinates for a red triangle centered around the middle in the custom coordinate system
triangle_points = [
    (0, -100),  # Top point of the triangle in custom coordinates
    (-86.6, 50),  # Bottom left
    (86.6, 50)  # Bottom right
]
dwg.add(dwg.polygon(points=triangle_points, fill='red'))
'''


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

#TODO rank by x,y

print("Draw cells")


colm0 = average_color(col1,col2)
colm1 = average_color(col0,col2)
colm2 = average_color(col0,col1)


for cell in cells:
    t = cell['T']
    t = t / max_pop
    if t>1: t=1
    t = pow(t, 0.23)
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

    dwg.add(dwg.circle(center=(cell['x'], y_min + y_max - cell['y']), r=diameter/2, fill=color))

print("Save SVG", res)
dwg.save()

#print("Save PDF", res)
#cairosvg.svg2pdf(url=path_svg, write_to=path_pdf)
