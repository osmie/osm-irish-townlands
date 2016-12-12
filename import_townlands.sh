#! /bin/bash

set -o errexit
set -o nounset

BASEDIR=$(dirname $0)
cd ${BASEDIR}
DB_USER=$1
DB_PASS=$2
OSM2PGSQL_CACHE=1000M

VERBOSE=""
QUICK=0
WGET_VERBOSE_ARG=" -q "     # by default no wget output
if [[ "$#" -ge 3 ]] ; then 
    VERBOSE=$3
    if [[ ! -z $VERBOSE ]] ; then
        set -x
        OSM2PGSQL_CACHE=1200M
        WGET_VERBOSE_ARG=""     # we want to see wget
        if [[ $VERBOSE == "quick" ]] ; then
            QUICK=1
        fi
    fi
fi


POSTGIS_CMD="psql -q -U ${DB_USER} -h localhost -d townlands"

# In case these are still around
for TABLE in planet_osm_nodes planet_osm_rels planet_osm_ways planet_osm_line planet_osm_line planet_osm_point planet_osm_roads planet_osm_polygon planet_osm_roads_tmp; do
	PGOPTIONS="--client-min-messages=warning" PGPASSWORD=$DB_PASS $POSTGIS_CMD -c "drop table if exists $TABLE;"
done

PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "CREATE EXTENSION IF NOT EXISTS hstore;" 2>/dev/null
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "CREATE EXTENSION IF NOT EXISTS postgis;" 2>/dev/null

wget ${WGET_VERBOSE_ARG} -N http://planet.openstreetmap.ie/ireland-and-northern-ireland.osm.pbf || wget -q -O ireland-and-northern-ireland.osm.pbf -N http://download.geofabrik.de/europe/ireland-and-northern-ireland-latest.osm.pbf || echo "Could not download"

FILENAME=ireland-and-northern-ireland.osm.pbf
if [[ $VERBOSE ]] ; then
    if [[ $QUICK == 1 ]] ; then
        # Only import carlow
        rm -f carlow.osm.pbf
        osmosis --read-pbf ./ireland-and-northern-ireland.osm.pbf --bounding-box left=-7.094 bottom=52.504 right=-6.713 top=52.852 completeWays=yes completeRelations=yes cascadingRelations=yes --write-pbf ./carlow.osm.pbf
        FILENAME=carlow.osm.pbf
    fi
    PGPASSWORD=${DB_PASS} osm2pgsql --hstore-all --latlong --username ${DB_USER} --host localhost --database townlands --cache ${OSM2PGSQL_CACHE} --cache-strategy sparse --slim --style ${BASEDIR}/townlands.style -G ${FILENAME}
else
    PGPASSWORD=${DB_PASS} osm2pgsql --hstore-all --latlong --username ${DB_USER} --host localhost --database townlands --cache ${OSM2PGSQL_CACHE} --cache-strategy sparse --slim --style ${BASEDIR}/townlands.style -G ${FILENAME} &>/dev/null
fi

# not needed anymore
for TABLE in planet_osm_nodes planet_osm_rels planet_osm_ways planet_osm_line planet_osm_line planet_osm_roads; do
	PGOPTIONS="--client-min-messages=warning" PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "drop table if exists $TABLE;"
done

# Add hstore indexes
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "CREATE INDEX plantet_osm_polygon__tags ON planet_osm_polygon using gist (tags);" 2>/dev/null
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "CREATE INDEX plantet_osm_point__tags ON planet_osm_point using gist (tags);" 2>/dev/null

# temporary clean up
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "delete from planet_osm_point where not ( COALESCE(place, '') = 'locality' and COALESCE(locality, '') = 'subtownland' );" 2>/dev/null

PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "drop table valid_polygon;" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create table if not exists valid_polygon (like planet_osm_polygon);" 2>/dev/null
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "insert into valid_polygon select * from planet_osm_polygon where name IS NOT NULL and st_isvalid(way) and not st_isempty(way) and (admin_level is not null or boundary is not null)";
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "alter table valid_polygon add column gid serial not null primary key;"
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "GRANT SELECT ON valid_polygon TO tirex;" || true

PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "drop table water_polygon;" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create table if not exists water_polygon (way geometry(MultiPolygon, 4326), geo geography);" 2>/dev/null
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
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "alter table valid_polygon add column geo geography;" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "update valid_polygon set geo = way::geography;"
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "vacuum full valid_polygon;" 2>/dev/null || true

PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "alter table water_polygon add column geo geography;" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "update water_polygon set geo = way::geography;" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "analyze water_polygon;" 2> /dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "cluster water_polygon using water_polygon__way;" 2> /dev/null || true

# Calculate the coastline
# Long line in case osmcoastline segfaults (has happened to me), I don't want
# to remove the old land_polygons shapefiles if that command doesn't succeed,
# so abuse bash this way
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "drop table land_polygons;" 2> /dev/null || true
rm -f coastline.db && osmcoastline -s 4326 -o coastline.db ireland-and-northern-ireland.osm.pbf >/dev/null && (cd ${BASEDIR}/data/ && rm -f land_polygons.dbf land_polygons.prj land_polygons.shp land_polygons.shx ) && ogr2ogr -f PostgreSQL PG:"dbname=townlands user=${DB_USER} password=${DB_PASS}" coastline.db land_polygons -overwrite -lco OVERWRITE=YES -nlt MULTIPOLYGON && ogr2ogr -f "ESRI Shapefile" ${BASEDIR}/data/land_polygons.shp coastline.db land_polygons && split-large-polygons -q -d townlands -t land_polygons -c wkb_geometry -i ogc_fid -a 0.001 -s 4326 && (cd ${BASEDIR}/data/ && rm -f land_polygons.dbf land_polygons.prj land_polygons.shp land_polygons.shx ) && pgsql2shp -f ${BASEDIR}/data/land_polygons.shp townlands land_polygons >/dev/null
rm -f coastline.db

# Make the split table
# Split polygons
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "drop table valid_polygon_split; " 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create table valid_polygon_split (gid serial primary key, admin_level text, boundary text, osm_id bigint, geom geometry(MultiPolygon, 4326));" 2> /dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "insert into valid_polygon_split (admin_level, boundary, osm_id, geom) select admin_level, boundary, osm_id, St_multi(way) from valid_polygon;" 2> /dev/null || true
split-large-polygons -q -d townlands -t valid_polygon_split -c geom -i gid -a 0.001 -s 4326

# Split water
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "drop table water_polygon_split; " 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create table water_polygon_split (gid serial primary key, geom geometry(MultiPolygon, 4326));" 2> /dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "insert into water_polygon_split (geom) select way from water_polygon;" 2> /dev/null || true
split-large-polygons -q -d townlands -t water_polygon_split -c geom -i gid -a 0.001 -s 4326
rm -rf ${BASEDIR}/data/water_polygon.*
ogr2ogr -f "ESRI Shapefile" ${BASEDIR}/data/water_polygon.shp PG:"dbname=townlands user=${DB_USER} password=${DB_PASS}" "water_polygon_split"
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "drop table water_polygon_split; " 2>/dev/null || true

pgsql2shp -f ${BASEDIR}/data/counties_split.shp townlands "select * from valid_polygon_split where admin_level = '6'" >/dev/null
pgsql2shp -f ${BASEDIR}/data/baronies_split.shp townlands "select * from valid_polygon_split where boundary = 'barony'" >/dev/null
pgsql2shp -f ${BASEDIR}/data/civil_parishes_split.shp townlands "select * from valid_polygon_split where boundary = 'civil_parish'" >/dev/null
pgsql2shp -f ${BASEDIR}/data/eds_split.shp townlands "select * from valid_polygon_split where admin_level = '9'" >/dev/null
pgsql2shp -f ${BASEDIR}/data/townlands_split.shp townlands "select * from valid_polygon_split where admin_level = '10'" >/dev/null
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "drop table valid_polygon_split; " 2>/dev/null || true

# Land not covered by...
difference-polygons -q -l ${BASEDIR}/data/land_polygons.shp  -r ${BASEDIR}/data/counties_split.shp -o ${BASEDIR}/data/not_counties.shp -a 1e-09
difference-polygons -q -l ${BASEDIR}/data/land_polygons.shp  -r ${BASEDIR}/data/baronies_split.shp -o ${BASEDIR}/data/not_baronies.shp -a 1e-09
difference-polygons -q -l ${BASEDIR}/data/land_polygons.shp  -r ${BASEDIR}/data/civil_parishes_split.shp -o ${BASEDIR}/data/not_civil_parishes.shp -a 1e-09
difference-polygons -q -l ${BASEDIR}/data/land_polygons.shp  -r ${BASEDIR}/data/eds_split.shp -o ${BASEDIR}/data/not_eds.shp -a 1e-09

# Not covered by townlands. NB unlike the previous boundaries, townlands traditionally don't include water areas
difference-polygons -q -l ${BASEDIR}/data/land_polygons.shp  -r ${BASEDIR}/data/townlands_split.shp -r ${BASEDIR}/data/water_polygon.shp -o ${BASEDIR}/data/not_townlands.shp -a 1e-09
