import svgwrite
import csv

# A0 dimensions in millimeters (landscape)
width_mm = 1189
height_mm = 841

# Custom coordinate system extents
x_min, x_max = 2297000, 6817000
y_min, y_max = 1442000, 5962000
viewBox_width = x_max - x_min
viewBox_height = y_max - y_min

# Create an SVG drawing object with A0 dimensions in landscape orientation
dwg = svgwrite.Drawing('/home/juju/Bureau/map.svg', size=(f'{width_mm}mm', f'{height_mm}mm'))

# Set the viewBox attribute to map the custom coordinates to the SVG canvas
dwg.viewbox(x_min, y_min, viewBox_width, viewBox_height)

# Set the background color to white
#dwg.add(dwg.rect(insert=(x_min, y_min), size=(viewBox_width, viewBox_height), fill='white'))

# Draw a yellow circle with a 10 cm (100 mm) radius at the center of the custom coordinate system
#dwg.add(dwg.circle(center=(5000000, 3000000), r=1000000, fill='blue'))

'''
# Coordinates for a red triangle centered around the middle in the custom coordinate system
triangle_points = [
    (0, -100),  # Top point of the triangle in custom coordinates
    (-86.6, 50),  # Bottom left
    (86.6, 50)  # Bottom right
]
dwg.add(dwg.polygon(points=triangle_points, fill='red'))
'''


print("Load cell data")
cells = []
with open('/home/juju/geodata/census/csv_export.csv', mode='r', newline='') as file:
    csv_reader = csv.DictReader(file)

    for row in csv_reader:
        if row['T'] == '0': continue
        del row['fid']
        del row['M']
        del row['F']
        del row['EMP']
        del row['NAT']
        del row['EU_OTH']
        del row['OTH']
        del row['SAME']
        del row['CHG_IN']
        del row['CHG_OUT']
        id = row['GRD_ID']

        #CRS3035RES1000mN1000000E1966000
        id = id.replace("CRS3035RES1000mN", "")
        del row['GRD_ID']
        id = id.split("E")
        row['y'] = int(id[0])
        row['x'] = int(id[1])

        cells.append(row)


print(len(cells))
#print(cells[0])

#TODO rank by x,y

print("Draw cells")
for cell in cells:
    dwg.add(dwg.circle(center=(cell['x'], cell['y']), r=500, fill='black'))

print("Save")
dwg.save()
