import svgwrite
import csv
#import cairosvg


path_svg = '/home/juju/Bureau/map.svg'
path_pdf = '/home/juju/Bureau/map.pdf'
res = 5000
in_CSV = '/home/juju/gisco/grid_pop_c2021/EU_' + str(res) + '.csv'

# A0 dimensions in millimeters (landscape)
width_mm = 1189
height_mm = 841

# Custom coordinate system extents
x_min, x_max = 1351000, 5444000
y_min, y_max = 2435000, 6553000
dx = x_max - x_min
dy = y_max - y_min

# Create an SVG drawing object with A0 dimensions in landscape orientation
dwg = svgwrite.Drawing(path_svg, size=(f'{width_mm}mm', f'{height_mm}mm'))

# Set the viewBox attribute to map the custom coordinates to the SVG canvas
dwg.viewbox(x_min, y_min, dx, dy)

# Set the background color to white
#dwg.add(dwg.rect(insert=(x_min, y_min), size=(viewBox_width, viewBox_height), fill='white'))

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
        row['x'] = int(row['x'])
        row['y'] = int(row['y'])
        row['T'] = int(row['T'])
        cells.append(row)

print(len(cells))
print(cells[0])

#TODO rank by x,y

print("Draw cells")
for cell in cells:
    dwg.add(dwg.circle(center=(cell['x'], cell['y']), r=res/2, fill='black'))

print("Save SVG", res)
dwg.save()

#print("Save PDF", res)
#cairosvg.svg2pdf(url=path_svg, write_to=path_pdf)
