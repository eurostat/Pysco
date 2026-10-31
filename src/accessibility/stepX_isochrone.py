


# Filled polygons between break values (e.g., 5, 10, 15, 30 min = 300, 600, 900, 1800 s)
# See https://gdal.org/en/stable/programs/gdal_contour.html
gdal_contour -p -amin MIN_T -amax MAX_T \
  -fl 0 600 1200 1800 2400 3000 3600 999999 \
  /home/juju/gisco/accessibility/euro_access_healthcare_2026_CAR_S_1000m_v2026_10.tif /home/juju/Bureau/iso.gpkg

