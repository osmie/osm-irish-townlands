#! /bin/bash

set -o errexit

wget -q -N http://download.geofabrik.de/openstreetmap/europe/ireland-and-northern-ireland.osm.pbf
osm2pgsql --cache 50M --slim --style ./osm2pgsql.style -G ireland-and-northern-ireland.osm.pbf
rm ireland-and-northern-ireland.osm.pbf
PGOPTIONS="--client-min-messages=warning" psql -q -d gis -c "drop table if exists valid_polygon;"
psql -q -d gis -c "create table valid_polygon as select * from planet_osm_polygon where name IS NOT NULL and st_isvalid(way) and (admin_level is not null or boundary is not null)";

# not needed anymore
psql -q -d gis -c "drop table planet_osm_line; drop table planet_osm_point; drop table planet_osm_polygon; drop table planet_osm_roads;"
psql -q -d gis -c "drop table if exists planet_osm_nodes ; drop table if exists planet_osm_rels ; drop table if exists planet_osm_ways ;"

psql -q -d gis -c "create index valid_polygon_way on valid_polygon using GIST (way);"
psql -q -d gis -c "alter table valid_polygon add column geo geography;"
psql -q -d gis -c "update valid_polygon set geo = st_geographyfromtext(astext(transform(way, 4326)));"
