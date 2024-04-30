#convert to gpkg and reproject
ogr2ogr -t_srs EPSG:3035 input.osm europe.gpkg

#extract for road network
ogr2ogr -sql "SELECT geom,fid,highway,other_tags FROM lines WHERE highway IS NOT NULL" -dialect SQLite -nln lines /home/juju/geodata/OSM/europe_road_network_prep.gpkg /home/juju/geodata/OSM/europe.gpkg

