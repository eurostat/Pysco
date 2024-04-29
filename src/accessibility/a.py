from shapely.geometry import box


#define 50km partition
partition_size = 50000
x_part = 3950000
y_part = 2850000
partition_bbox = box(x_part, y_part, x_part+partition_size, y_part+partition_size)


#make buffered window around
extended_bbox = box(x_part-partition_size*0.5, y_part-partition_size*0.5, x_part+partition_size*1.5, y_part+partition_size*1.5)


#get road network in it
#get hospitals in it

#get populated grid cells in 50km partition

#for each grid cell, get 5 hospitals around - compute shortest path to nearest
#OR
#for each hospital, compute shortest path to cells around - or isochrones



