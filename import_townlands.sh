#! /bin/bash

set -o errexit
set -o nounset

BASEDIR=$(dirname $0)
cd ${BASEDIR}
DB_USER=$1
DB_PASS=$2
OSM2PGSQL_CACHE=200M

if [[ "$#" -gt 3 ]] ; then 
    VERBOSE=$3
    if [[ $VERBOSE ]] ; then
        set -x
        OSM2PGSQL_CACHE=1200M
    fi
fi


POSTGIS_CMD="psql -q -U ${DB_USER} -h localhost -d townlands"

# In case these are still around
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "drop table valid_polygon;" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "drop table water_polygon;" 2>/dev/null || true
for TABLE in planet_osm_nodes planet_osm_rels planet_osm_ways planet_osm_line planet_osm_line planet_osm_point planet_osm_roads planet_osm_polygon planet_osm_roads_tmp; do
	PGOPTIONS="--client-min-messages=warning" PGPASSWORD=$DB_PASS $POSTGIS_CMD -c "drop table if exists $TABLE;"
done


wget -q -N http://planet.openstreetmap.ie/ireland-and-northern-ireland.osm.pbf || wget -q -O ireland-and-northern-ireland.osm.pbf -N http://download.geofabrik.de/europe/ireland-and-northern-ireland-latest.osm.pbf || echo "Could not download"

if [[ $VERBOSE ]] ; then
    PGPASSWORD=${DB_PASS} osm2pgsql --username ${DB_USER} --host localhost --database townlands --cache ${OSM2PGSQL_CACHE} --cache-strategy sparse --slim --style ${BASEDIR}/townlands.style -G ireland-and-northern-ireland.osm.pbf
else
    PGPASSWORD=${DB_PASS} osm2pgsql --username ${DB_USER} --host localhost --database townlands --cache ${OSM2PGSQL_CACHE} --cache-strategy sparse --slim --style ${BASEDIR}/townlands.style -G ireland-and-northern-ireland.osm.pbf &>/dev/null
fi
#rm ireland-and-northern-ireland*.osm.pbf

# not needed anymore
for TABLE in planet_osm_nodes planet_osm_rels planet_osm_ways planet_osm_line planet_osm_line planet_osm_roads; do
	PGOPTIONS="--client-min-messages=warning" PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "drop table if exists $TABLE;"
done

# temporary clean up
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "delete from planet_osm_point where not ( place = 'locality' and locality = 'subtownland' );" 2>/dev/null

PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create table if not exists valid_polygon (like planet_osm_polygon);" 2>/dev/null
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "insert into valid_polygon select * from planet_osm_polygon where name IS NOT NULL and st_isvalid(way) and not st_isempty(way) and (admin_level is not null or boundary is not null)";

PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create table if not exists water_polygon (way geometry(MultiPolygon, 900913), geo geography);" 2>/dev/null
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "insert into water_polygon (way) select st_multi(way) from planet_osm_polygon where water IS NOT NULL OR waterway IS NOT NULL OR \"natural\" = 'water' and st_isvalid(way)";

PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "drop table planet_osm_polygon;"

PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create index valid_polygon__way on valid_polygon using GIST (way);" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create index valid_polygon__osm_id on valid_polygon (osm_id);" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create index valid_polygon__admin_level on valid_polygon (admin_level);" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create index valid_polygon__name on valid_polygon (name);" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create index valid_polygon__boundary on valid_polygon (boundary);" 2>/dev/null || true

PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create index water_polygon__way on water_polygon using GIST (way);" 2>/dev/null || true

# Index for each county
for COUNTY_NAME in Tyrone Kerry Dublin Down Fermanagh Wexford Mayo Carlow Wicklow Longford Westmeath Cork Leitrim Laois Waterford Tipperary Monaghan Kilkenny Galway Meath Donegal Cavan Kildare Offaly Londonderry Clare Armagh Antrim Limerick Louth Sligo Roscommon ; do
    PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create index valid_polygon__way_county_${COUNTY_NAME} on valid_polygon using GIST (way) where admin_level = '6' and name = 'County ${COUNTY_NAME}';" 2>/dev/null || true
done
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create index valid_polygon__way_10 on valid_polygon using GIST (way) where admin_level = '10';" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create index valid_polygon__way_9 on valid_polygon using GIST (way) where admin_level = '9';" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create index valid_polygon__way_barony on valid_polygon using GIST (way) where boundary = 'barony';" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create index valid_polygon__way_cp on valid_polygon using GIST (way) where boundary = 'civil_parish';" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "analyze valid_polygon;" 2>/dev/null || true


PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "alter table valid_polygon add column geo geography;" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "update valid_polygon set geo = st_transform(way, 4326)::geography;"

PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "alter table water_polygon add column geo geography;" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "update water_polygon set geo = st_transform(way, 4326)::geography;" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "analyze water_polygon;" 2> /dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "cluster water_polygon using water_polygon__way;" 2> /dev/null || true



cd ${BASEDIR}
#./screenshot-townlands.sh
