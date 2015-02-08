#! /bin/bash

set -o errexit
set -o nounset

BASEDIR=$(dirname $0)
cd ${BASEDIR}
DB_USER=$1
DB_PASS=$2
EXPORTED_FILES_DIR=$3

POSTGIS_CMD="psql -q -U ${DB_USER} -h localhost -d gis"

# In case these are still around
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "drop table valid_polygon;" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "drop table water_polygon;" 2>/dev/null || true
for TABLE in planet_osm_nodes planet_osm_rels planet_osm_ways planet_osm_line planet_osm_line planet_osm_point planet_osm_roads planet_osm_polygon planet_osm_roads_tmp; do
	PGOPTIONS="--client-min-messages=warning" PGPASSWORD=$DB_PASS $POSTGIS_CMD -c "drop table if exists $TABLE;"
done


wget -q -N http://planet.openstreetmap.ie/ireland-and-northern-ireland.osm.pbf
PGPASSWORD=${DB_PASS} osm2pgsql --username ${DB_USER} --host localhost --cache 200M --cache-strategy sparse --slim --style ${BASEDIR}/osm2pgsql.style -G ireland-and-northern-ireland.osm.pbf &>/dev/null
#rm ireland-and-northern-ireland.osm.pbf

# not needed anymore
for TABLE in planet_osm_nodes planet_osm_rels planet_osm_ways planet_osm_line planet_osm_line planet_osm_roads; do
	PGOPTIONS="--client-min-messages=warning" PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "drop table if exists $TABLE;"
done

# temporary clean up
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "delete from planet_osm_point where not ( place = 'locality' and locality = 'subtownland' );" 2>/dev/null

PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create table if not exists valid_polygon (like planet_osm_polygon);" 2>/dev/null
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "insert into valid_polygon select * from planet_osm_polygon where name IS NOT NULL and st_isvalid(way) and (admin_level is not null or boundary is not null)";

PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create table if not exists water_polygon (way geometry(MultiPolygon, 900913), geo geography);" 2>/dev/null
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "insert into water_polygon (way) select st_multi(way) from planet_osm_polygon where water IS NOT NULL OR waterway IS NOT NULL OR \"natural\" = 'water' and st_isvalid(way)";

PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "drop table planet_osm_polygon;"

PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create index valid_polygon__way on valid_polygon using GIST (way);" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create index valid_polygon__admin_level on valid_polygon (admin_level);" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create index valid_polygon__name on valid_polygon (name);" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create index water_polygon__way on water_polygon using GIST (way);" 2>/dev/null || true

# Index for each county
for COUNTY_NAME in Tyrone Kerry Dublin Down Fermanagh Wexford Mayo Carlow Wicklow Longford Westmeath Cork Leitrim Laois Waterford Tipperary Monaghan Kilkenny Galway Meath Donegal Cavan Kildare Offaly Londonderry Clare Armagh Antrim Limerick Louth Sligo Roscommon ; do
    PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "create index valid_polygon__way_county_${COUNTY_NAME} on valid_polygon using GIST (way) where admin_level = '6' and name = 'County ${COUNTY_NAME}';" 2>/dev/null || true
done


PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "alter table valid_polygon add column geo geography;" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "update valid_polygon set geo = st_transform(way, 4326)::geography;"

PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "alter table water_polygon add column geo geography;" 2>/dev/null || true
PGPASSWORD=${DB_PASS} $POSTGIS_CMD -c "update water_polygon set geo = st_transform(way, 4326)::geography;"

function dump() {
    PREFIX=$1
    WHERE=$2
    rm -f ${PREFIX}
    pgsql2shp -f ${PREFIX} -u "${DB_USER}" -P "${DB_PASS}" gis "select osm_id, name, \"name:ga\", \"name:en\", alt_name, \"alt_name:ga\", st_area(geo) as area_m2, ST_X(st_transform((ST_centroid(way)), 4326)) as latitude, ST_Y(st_transform((ST_centroid(way)), 4326)) as longitude, geo from valid_polygon where ${WHERE}" >/dev/null
}


# dump townlands etc as shapefiles
mkdir -p $EXPORTED_FILES_DIR
dump ${EXPORTED_FILES_DIR}/provinces "admin_level = '5'"
dump ${EXPORTED_FILES_DIR}/counties "admin_level = '6'"
dump ${EXPORTED_FILES_DIR}/townlands "admin_level = '10'"
dump ${EXPORTED_FILES_DIR}/baronies "boundary = 'barony'"
dump ${EXPORTED_FILES_DIR}/civil_parishes "boundary = 'civil_parish'"
dump ${EXPORTED_FILES_DIR}/eds "admin_level = '9'"

pushd ${EXPORTED_FILES_DIR} > /dev/null
for TYPE in townlands counties baronies civil_parishes provinces eds ; do

    ogr2ogr -f "GeoJSON" ${TYPE}.geojson ${TYPE}.shp
    zip -q ${TYPE}.geojson.zip ${TYPE}.geojson
    rm -f ${TYPE}.geojson

    rm -f doc.kml
    ogr2ogr -f "KML" doc.kml ${TYPE}.shp -dsco NameField=name
    zip -q ${TYPE}.kmz doc.kml
    rm -f doc.kml

    rm -f ${TYPE}.csv ${TYPE}.csv.zip
    ogr2ogr -f CSV ${TYPE}.csv ${TYPE}.shp -lco GEOMETRY=AS_WKT
    zip -q ${TYPE}.csv.zip ${TYPE}.csv
    rm -f ${TYPE}.csv

    zip -q ${TYPE}.zip ${TYPE}.dbf ${TYPE}.prj ${TYPE}.shp ${TYPE}.shx
    rm -f ${TYPE}.dbf ${TYPE}.prj ${TYPE}.shp ${TYPE}.shx
done
popd > /dev/null


cd ${BASEDIR}
#./screenshot-townlands.sh
