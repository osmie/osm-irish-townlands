#! /bin/bash

set -o errexit
set -o nounset

BASEDIR=$(dirname $0)
cd ${BASEDIR}
DB_USER=$1
DB_PASS=$2

POSTGIS_CMD="psql -q -U ${DB_USER} -h localhost -d gis"

# In case these are still around
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "truncate table valid_polygon;" || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "truncate table water_polygon;" || true
#for TABLE in planet_osm_nodes planet_osm_rels planet_osm_ways planet_osm_line planet_osm_line planet_osm_point planet_osm_roads planet_osm_polygon planet_osm_roads_tmp; do
#	PGOPTIONS="--client-min-messages=warning" PGPASSWORD=$DB_PASS $POSTGIS_CMD -c "drop table if exists $TABLE;"
#done
#
#
#wget -q -N http://download.geofabrik.de/europe/ireland-and-northern-ireland-latest.osm.pbf
#PGPASSWORD=${DB_PASS} osm2pgsql --username ${DB_USER} --host localhost --cache 200M --cache-strategy sparse --slim --style ./osm2pgsql.style -G ireland-and-northern-ireland-latest.osm.pbf
#rm ireland-and-northern-ireland-latest.osm.pbf
#
## not needed anymore
#for TABLE in planet_osm_nodes planet_osm_rels planet_osm_ways planet_osm_line planet_osm_line planet_osm_point planet_osm_roads; do
#	PGOPTIONS="--client-min-messages=warning" PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "drop table if exists $TABLE;"
#done

PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create table if not exists valid_polygon (like planet_osm_polygon);"
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "insert into valid_polygon select * from planet_osm_polygon where name IS NOT NULL and st_isvalid(way) and (admin_level is not null or boundary is not null)";

PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create table if not exists water_polygon (way geometry(MultiPolygon, 900913), geo geography);"
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "insert into water_polygon (way) select st_multi(way) from planet_osm_polygon where water IS NOT NULL OR waterway IS NOT NULL OR \"natural\" = 'water' and st_isvalid(way)";

PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "drop table planet_osm_polygon;"

#PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create index valid_polygon__way on valid_polygon using GIST (way); create index valid_polygon__admin_level on valid_polygon (admin_level); create index valid_polygon__name on valid_polygon (name);"
#PGPASSWORD=${DB_PASS} $POSTGIS_CM -c "create index water_polygon__way on water_polygon using GIST (way);"

PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "alter table valid_polygon add column geo geography;" || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "update valid_polygon set geo = st_geographyfromtext(st_astext(st_transform(way, 4326)));"

PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "alter table water_polygon add column geo geography;" || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "update valid_polygon set geo = st_geographyfromtext(st_astext(st_transform(way, 4326)));"

cd ${BASEDIR}
#./screenshot-townlands.sh
