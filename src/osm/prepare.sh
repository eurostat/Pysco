#convert to gpkg and reproject
ogr2ogr -t_srs EPSG:3035 input.osm europe.gpkg

#extract information for road network
ogr2ogr -sql "SELECT geom,fid,highway,other_tags FROM lines WHERE highway IS NOT NULL" -dialect SQLite -nln lines /home/juju/geodata/OSM/europe_road_network_prep.gpkg /home/juju/geodata/OSM/europe.gpkg

#extract information for buildings
ogr2ogr -sql "SELECT geom,fid,building,other_tags FROM multipolygons WHERE building IS NOT NULL" -dialect SQLite -nln multipolygons /home/juju/geodata/OSM/europe_road_buildings_prep.gpkg /home/juju/geodata/OSM/europe.gpkg
