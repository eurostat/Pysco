import svgwrite
import csv
#import cairosvg


path_svg = '/home/juju/Bureau/map.svg'
path_pdf = '/home/juju/Bureau/map.pdf'
res = 10000
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

# Create an SVG drawing object with A0 dimensions in landscape orientation
dwg = svgwrite.Drawing(path_svg, size=(f'{width_mm}mm', f'{height_mm}mm'))

# Set the viewBox attribute to map the custom coordinates to the SVG canvas
dwg.viewbox(x_min, y_min, width_m, height_m)

# Set the background color to white
dwg.add(dwg.rect(insert=(x_min, y_min), size=(width_m, height_m), fill='#dfdfdf'))

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

print(len(cells))
print(cells[0])

#TODO rank by x,y

print("Draw cells")
min_diameter = 0.2 / 1000 / scale
max_diameter = res * 1.2
#print(min_diameter, max_diameter)
for cell in cells:
    t = cell['T']
    t = t / max_pop
    if t>1: t=1
    t = pow(t, 0.23)
    diameter = min_diameter + t * (max_diameter - min_diameter)

    p0 = int(cell['Y_LT15'])
    p1 = int(cell['Y1564'])
    p2 = int(cell['Y_GE65'])
    t = cell['T']
    t_ = p0 + p1 + p2
    print(t,t_)

    if t != t_: color = "red"
    else:
        #TODO
        color = "black"

    dwg.add(dwg.circle(center=(cell['x'], y_min + y_max - cell['y']), r=diameter/2, fill=color))

print("Save SVG", res)
dwg.save()

#print("Save PDF", res)
#cairosvg.svg2pdf(url=path_svg, write_to=path_pdf)
