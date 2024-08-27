import svgwrite
import fiona


path_svg = '/home/juju/gisco/census_2021_map/map_age_labels.svg'
gpkg_path = '/home/juju/gisco/census_2021_map/labels_filtered.gpkg'
font_name='Myriad'
font_size=16


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



dwg = svgwrite.Drawing(path_svg, size=(f'{width_mm}mm', f'{height_mm}mm'))

# Create group elements
g = dwg.g(id='boundaries', transform=transform_str, font_family=font_name, font_size=font_size, fill='black')
dwg.add(g)


print("Make map")
layer = fiona.open(gpkg_path)
for feature in layer:
    coords = feature['geometry']['coordinates']
    x, y = coords
    name = feature['properties']['name']

    g.add(dwg.text(
        name,
        insert=(x, y),
    ))

print("Save")
dwg.save()
