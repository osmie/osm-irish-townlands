from django.conf import settings
import subprocess
import os

from django.core.management.base import BaseCommand, CommandError

def rm(*paths):
    for path in paths:
        if os.path.exists(path):
            os.remove(path)

def zip(filename, zipfile=None):
    zipfile = zipfile or filename+".zip"
    subprocess.call(["zip", "-q", zipfile, filename])
    rm(filename)

def dump(directory, file_prefix, dbuser, dbpass, query):
    os.chdir(directory)
    subprocess.call(["pgsql2shp", "-f", file_prefix, "-u", dbuser, "-h", "localhost", "-P", dbpass, "townlands", query], stdout=subprocess.PIPE)

    # Convert
    rm(file_prefix+".geojson")
    subprocess.call(["ogr2ogr", "-f", "GeoJSON", file_prefix+".geojson", file_prefix+".shp"])
    zip(file_prefix+".geojson")

    rm("doc.kml")
    subprocess.call(["ogr2ogr", "-f", "KML", "doc.kml", file_prefix+".shp", "-dsco", "NameField=name"])
    zip("doc.kml", file_prefix+".kmz")

    rm(file_prefix+".csv", file_prefix+".csv.zip")
    subprocess.call(["ogr2ogr", "-f", "CSV", file_prefix+".csv", file_prefix+".shp", "-lco", "GEOMETRY=AS_WKT"])
    zip(file_prefix+".csv")

    rm(file_prefix+"-no-geom.csv", file_prefix+"-no-geom.csv.zip")
    subprocess.call(["ogr2ogr", "-f", "CSV", file_prefix+"-no-geom.csv", file_prefix+".shp"])
    zip(file_prefix+"-no-geom.csv")

    subprocess.call(["zip", "-q", file_prefix+".zip", file_prefix+".dbf", file_prefix+".prj", file_prefix+".shp", file_prefix+".shx"])
    rm(file_prefix+".dbf", file_prefix+".prj", file_prefix+".shp", file_prefix+".shx")

class Command(BaseCommand):
    def handle(self, *args, **options):
        directory = args[0]
        dbuser = settings.DATABASES['default']['USER']
        dbpass = settings.DATABASES['default']['PASSWORD']


        dump(directory, "townlands", dbuser, dbpass, """
            SELECT
                xx.*, ST_Area(xx.geom::geography) AS area,
                ST_Y(ST_Centroid(xx.geom)) AS latitude, ST_X(ST_Centroid(xx.geom)) AS longitude,
                EXTRACT(epoch FROM osm_timestamp) AS epoch_tstmp
            FROM (
                SELECT
                    t.osm_id, t.name, t.name_ga, t.name_en, t.alt_name, t.alt_name_ga,
                    t.osm_user, t.osm_timestamp, c.name AS co_name, c.osm_id AS co_osm_id,
                    cp.name AS cp_name, cp.osm_id AS cp_osm_id, ed.name AS ed_name,
                    ed.osm_id AS ed_osm_id, b.name AS bar_name, b.osm_id AS bar_osm_id,
                    CONCAT('http://www.townlands.ie/', t.url_path) AS t_ie_url,
                    ST_GeomFromGeoJSON(irish_townlands_polygon.polygon_geojson) AS geom
                FROM
                    irish_townlands_townland AS t
                        JOIN irish_townlands_polygon ON (t._polygon_geojson_id = irish_townlands_polygon.id)
                    LEFT OUTER JOIN irish_townlands_county AS c
                        ON (t.county_id = c.id)
                    LEFT OUTER JOIN irish_townlands_barony AS b
                        ON (t.barony_id = b.id)
                    LEFT OUTER JOIN irish_townlands_civilparish AS cp
                        ON (cp.id = t.civil_parish_id)
                    LEFT OUTER JOIN irish_townlands_electoraldivision AS ed
                        ON (ed.id = t.ed_id)
                ) AS xx
            """)
        dump(directory, "counties", dbuser, dbpass, """
            SELECT
                xx.*, ST_area(xx.geom::geography) AS area,
                ST_Y(ST_Centroid(xx.geom)) AS latitude, ST_X(ST_Centroid(xx.geom)) AS longitude,
                EXTRACT(epoch FROM osm_timestamp) AS epoch_tstmp
            FROM (
                SELECT
                    c.osm_id, c.name, c.name_ga, c.name_en, c.alt_name, c.alt_name_ga,
                    c.osm_user, c.osm_timestamp,
                    CONCAT('http://www.townlands.ie/', c.url_path) AS t_ie_url,
                    ST_GeomFromGeoJSON(irish_townlands_polygon.polygon_geojson) AS geom
                FROM
                    irish_townlands_county AS c
                        JOIN irish_townlands_polygon
                        ON (c._polygon_geojson_id = irish_townlands_polygon.id)
            ) AS xx
             """)
        dump(directory, "baronies", dbuser, dbpass, """
            SELECT
                xx.*, ST_Area(xx.geom::geography) AS area, ST_Y(ST_Centroid(xx.geom)) AS latitude,
                ST_X(ST_Centroid(xx.geom)) AS longitude,
                EXTRACT(epoch FROM osm_timestamp) AS epoch_tstmp
            FROM (
                SELECT
                    b.osm_id, b.name, b.name_ga, b.name_en, b.alt_name,
                    b.alt_name_ga, b.osm_user, b.osm_timestamp, c.name AS co_name,
                    c.osm_id AS co_osm_id,
                    CONCAT('http://www.townlands.ie/', b.url_path) AS t_ie_url,
                    ST_GeomFromGeoJSON(irish_townlands_polygon.polygon_geojson) AS geom
                FROM
                    irish_townlands_barony AS b
                        JOIN irish_townlands_polygon ON (b._polygon_geojson_id = irish_townlands_polygon.id)
                    LEFT OUTER JOIN irish_townlands_county AS c
                        ON (b.county_id = c.id)
                ) AS xx
             """)
        dump(directory, "civil_parishes", dbuser, dbpass, "select xx.*, st_area(xx.geom::geography) as area, st_y(st_centroid(xx.geom)) as latitude, st_x(st_centroid(xx.geom)) as longitude, extract(epoch from osm_timestamp) as epoch_tstmp from (select cp.osm_id, cp.name, cp.name_ga, cp.name_en, cp.alt_name, cp.alt_name_ga, cp.osm_user, cp.osm_timestamp, c.name as co_name, c.osm_id as co_osm_id, concat('http://www.townlands.ie/', cp.url_path) as t_ie_url,  st_geomfromgeojson(irish_townlands_polygon.polygon_geojson) as geom from irish_townlands_civilparish as cp join irish_townlands_polygon on (cp._polygon_geojson_id = irish_townlands_polygon.id) left outer join irish_townlands_county as c on (cp.county_id = c.id)) as xx")
        dump(directory, "eds", dbuser, dbpass, "select xx.*, st_area(xx.geom::geography) as area, st_y(st_centroid(xx.geom)) as latitude, st_x(st_centroid(xx.geom)) as longitude, extract(epoch from osm_timestamp) as epoch_tstmp from (select ed.osm_id, ed.name, ed.name_ga, ed.name_en, ed.alt_name, ed.alt_name_ga, ed.osm_user, ed.osm_timestamp, c.name as co_name, c.osm_id as co_osm_id, concat('http://www.townlands.ie/', ed.url_path) as t_ie_url,  st_geomfromgeojson(irish_townlands_polygon.polygon_geojson) as geom from irish_townlands_electoraldivision as ed join irish_townlands_polygon on (ed._polygon_geojson_id = irish_townlands_polygon.id) left outer join irish_townlands_county as c on (ed.county_id = c.id)) as xx")

