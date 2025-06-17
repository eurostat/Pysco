
# combine all tiff into a single one
# band on nearby pop, accessible pop, ratio

from utils.geotiff import combine_geotiffs


out_folder = '/home/juju/gisco/road_transport_performance/'
year = "2021"
grid_resolution = 1000

geotiff_ap = out_folder + "accessible_population_" + year + "_" + str(grid_resolution) + "m.tif"
geotiff_np = out_folder + "nearby_population_" + year + "_" + str(grid_resolution) + "m.tif"
combined = out_folder + "combined_" + year + "_" + str(grid_resolution) + "m.tif"

print("combine geotiff")
combine_geotiffs([geotiff_np, geotiff_ap], combined, compress="deflate")


#print("rename tiff bands")
#rename_geotiff_bands(geotiff, [service + "_" + year + "_1", service + "_" + year + "_a3"])

