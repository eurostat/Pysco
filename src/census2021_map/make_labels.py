import svgwrite
import fiona


path_svg = '/home/juju/gisco/census_2021_map/map_age_labels.svg'
gpkg_path = '/home/juju/gisco/census_2021_map/labels_filtered.gpkg'
font_name='Myriad'

# transform for europe view
# A0 dimensions in millimeters (landscape)
scale = 1/5000000
width_mm = 1189
height_mm = 841
width_px = width_mm * 96 / 25.4
height_px = height_mm * 96 / 25.4

cx = 3700000
cy = 3400000
width_m = width_mm / scale / 1000
height_m = height_mm / scale / 1000
x_min, x_max = cx - width_m/2, cx + width_m/2
y_min, y_max = cy - height_m/2, cy + height_m/2
#transform_str = f"scale({scale*1000*96/25.4} {scale*1000*96/25.4}) translate({-x_min} {-y_min})"



dwg = svgwrite.Drawing(path_svg, size=(f'{width_px}px', f'{height_px}px'))
#dwg.viewbox(x_min, y_min, width_m, height_m)


# Create group elements
g = dwg.g(id='boundaries', font_family=font_name, fill='black')
#, transform=transform_str
dwg.add(g)

def geoToPixX(xg):
    return (xg-x_min)/width_m * width_px
def geoToPixY(yg):
    return (1-(yg-y_min)/height_m) * height_px


print("Make map")
layer = fiona.open(gpkg_path)
for feature in layer:
    cc = feature['properties']['cc']
    if cc=="UK": continue
    if cc=="UA": continue
    if cc=="RS": continue
    if cc=="BA": continue
    if cc=="AL": continue
    if cc=="ME": continue
    x, y = feature['geometry']['coordinates']
    name = feature['properties']['name']
    r1 = feature['properties']['r1']
    font_size=13 if r1<800 else 16
    g.add(dwg.text(name, insert=(round(geoToPixX(x)), round(geoToPixY(y))), font_size=font_size))
    #g.add(dwg.text(name, insert=(width_px/2, height_px/2)))

print("Save")
dwg.save()
