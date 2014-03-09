#! /bin/bash

set -o errexit

cd $(dirname $0)

PGOPTIONS="--client-min-messages=warning" psql -q -d gis -c "drop table if exists valid_polygon;"
PGOPTIONS="--client-min-messages=warning" psql -q -d gis -c "drop table if exists water_polygon;"

wget -q -N http://download.geofabrik.de/openstreetmap/europe/ireland-and-northern-ireland.osm.pbf
osm2pgsql --cache 50M --slim --style ./osm2pgsql.style -G ireland-and-northern-ireland.osm.pbf
rm ireland-and-northern-ireland.osm.pbf

# not needed anymore
psql -q -d gis -c "drop table if exists planet_osm_nodes ; drop table if exists planet_osm_rels ; drop table if exists planet_osm_ways ;"
psql -q -d gis -c "drop table planet_osm_line; drop table planet_osm_point; drop table planet_osm_roads;"

psql -q -d gis -c "create table valid_polygon as select * from planet_osm_polygon where name IS NOT NULL and st_isvalid(way) and (admin_level is not null or boundary is not null)";
psql -q -d gis -c "create table water_polygon as select way from planet_osm_polygon where water IS NOT NULL OR waterway IS NOT NULL OR \"natural\" = 'water' and st_isvalid(way)";

psql -q -d gis -c "drop table planet_osm_polygon;"


psql -q -d gis -c "create index valid_polygon__way on valid_polygon using GIST (way); create index valid_polygon__admin_level on valid_polygon (admin_level); create index valid_polygon__name on valid_polygon (name);"
psql -q -d gis -c "create index water_polygon__way on water_polygon using GIST (way);"

psql -q -d gis -c "alter table valid_polygon add column geo geography;"
psql -q -d gis -c "update valid_polygon set geo = st_geographyfromtext(astext(transform(way, 4326)));"

psql -q -d gis -c "alter table water_polygon add column geo geography;"
psql -q -d gis -c "update valid_polygon set geo = st_geographyfromtext(astext(transform(way, 4326)));"
