from django.conf import settings
import subprocess
import os, os.path
import csv
import psycopg2

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

def townland_touching(directory, dbuser, dbpass):
    conn = psycopg2.connect(host='127.0.0.1', database="townlands", user=dbuser, password=dbpass)
    cursor = conn.cursor()

    with open(os.path.join(directory, "townlandtouch.csv"), "w") as fp:
        csvwriter = csv.writer(fp, lineterminator="\n")
        csvwriter.writerow(["t1_osm_id", "t2_osm_id", "direction", "length_m"])
        cursor.execute("select t1.osm_id as t1_osm_id, t2.osm_id as t2_osm_id, tt.direction_radians * 57.2957795 as direction, tt.length_m from irish_townlands_townlandtouch as tt join irish_townlands_townland as t1 on (tt.townland_a_id = t1.id) join irish_townlands_townland as t2 on (tt.townland_b_id = t2.id);")
        for row in cursor:
            csvwriter.writerow(row)

    zip("townlandtouch.csv")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("directory")

    def handle(self, *args, **options):
        directory = options['directory']
        os.chdir(directory)

        dbuser = settings.DATABASES['default']['USER']
        dbpass = settings.DATABASES['default']['PASSWORD']


        # There is some weird quoting things going on, requireing me to split
        # the query into 2 parts. If it was all """....""" then there's a
        # postgres syntax error at 'http://'

        dump(directory, "townlands", dbuser, dbpass,
            """SELECT xx.*, ST_Area(xx.geom::geography) AS area,
                ST_Y(ST_Centroid(xx.geom)) AS latitude, ST_X(ST_Centroid(xx.geom)) AS longitude,
                EXTRACT(epoch FROM osm_timestamp) AS epoch_tstmp
            FROM (
                SELECT
                    t.osm_id, t.name, t.name_ga, t.name_en, t.alt_name, t.alt_name_ga,
                    t.osm_user, t.osm_timestamp, t.attribution,
                    c.name AS co_name, c.osm_id AS co_osm_id, cp.name AS cp_name,
                    cp.osm_id AS cp_osm_id, ed.name AS ed_name,
                    ed.osm_id AS ed_osm_id, b.name AS bar_name, b.osm_id AS bar_osm_id,
                    concat('http://www.townlands.ie/', t.url_path) AS t_ie_url,
                    ST_SetSRID(ST_GeomFromGeoJSON(irish_townlands_polygon.polygon_geojson), 4326) AS geom
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
                ) AS xx;""")

        dump(directory, "counties", dbuser, dbpass,
            """SELECT xx.*, ST_area(xx.geom::geography) AS area,
                ST_Y(ST_Centroid(xx.geom)) AS latitude, ST_X(ST_Centroid(xx.geom)) AS longitude,
                EXTRACT(epoch FROM osm_timestamp) AS epoch_tstmp
            FROM (
                SELECT
                    c.osm_id, c.name, c.name_ga, c.name_en, c.alt_name, c.alt_name_ga,
                    c.osm_user, c.osm_timestamp, c.attribution,
                    concat('http://www.townlands.ie/', c.url_path) AS t_ie_url,
                    ST_SetSRID(ST_GeomFromGeoJSON(irish_townlands_polygon.polygon_geojson), 4326) AS geom
                FROM
                    irish_townlands_county AS c
                        JOIN irish_townlands_polygon
                        ON (c._polygon_geojson_id = irish_townlands_polygon.id)
            ) AS xx
             """)

        dump(directory, "baronies", dbuser, dbpass,
            """SELECT 
                xx.*, ST_Area(xx.geom::geography) AS area, ST_Y(ST_Centroid(xx.geom)) AS latitude,
                ST_X(ST_Centroid(xx.geom)) AS longitude,
                EXTRACT(epoch FROM osm_timestamp) AS epoch_tstmp
            FROM (
                SELECT
                    b.osm_id, b.name, b.name_ga, b.name_en, b.alt_name,
                    b.alt_name_ga, b.osm_user, b.osm_timestamp, b.attribution,
                    c.name AS co_name, c.osm_id AS co_osm_id,
                    concat('http://www.townlands.ie/', b.url_path) AS t_ie_url,
                    ST_SetSRID(ST_GeomFromGeoJSON(irish_townlands_polygon.polygon_geojson), 4326) AS geom
                FROM
                    irish_townlands_barony AS b
                        JOIN irish_townlands_polygon ON (b._polygon_geojson_id = irish_townlands_polygon.id)
                    LEFT OUTER JOIN irish_townlands_county AS c
                        ON (b.county_id = c.id)
                ) AS xx
             """)

        # A minority of civil parishes overlap county borders.
        dump(directory, "civil_parishes", dbuser, dbpass,
            "SELECT "+
                """xx.*, ST_Area(xx.geom::geography) AS area,
                ST_Y(ST_Centroid(xx.geom)) AS latitude, ST_X(ST_Centroid(xx.geom)) AS longitude,
                EXTRACT(epoch FROM osm_timestamp) AS epoch_tstmp
            FROM (
                SELECT
                    cp.osm_id, cp.name, cp.name_ga, cp.name_en, cp.alt_name, cp.alt_name_ga,
                    cp.osm_user, cp.osm_timestamp, cp.attribution,
                    c.c_names as co_names, c.c_osm_ids as co_osm_ids,
                    concat('http://www.townlands.ie/', cp.url_path) AS t_ie_url,
                    ST_SetSRID(ST_GeomFromGeoJSON(irish_townlands_polygon.polygon_geojson), 4326) AS geom
                FROM
                    irish_townlands_civilparish AS cp
                        JOIN irish_townlands_polygon ON (cp._polygon_geojson_id = irish_townlands_polygon.id)
                    LEFT OUTER JOIN (

                        SELECT
                            cp.id,
                            STRING_AGG(c.name, ', ' ORDER BY c.name) AS c_names,
                            STRING_AGG(c.osm_id::text, ', ' ORDER by c.name) AS c_osm_ids
                        FROM
                            irish_townlands_civilparish AS cp
                            JOIN irish_townlands_civilparish_counties AS m2m
                                ON (cp.id = m2m.civilparish_id)
                            JOIN irish_townlands_county AS c
                                ON (c.id = m2m.county_id)
                        GROUP BY cp.id

                        ) as c ON (cp.id = c.id)
            ) AS xx
            """)

        dump(directory, "eds", dbuser, dbpass,
            """SELECT 
                xx.*, ST_Area(xx.geom::geography) AS area,
                ST_Y(ST_Centroid(xx.geom)) AS latitude, ST_X(ST_Centroid(xx.geom)) AS longitude,
                EXTRACT(epoch FROM osm_timestamp) AS epoch_tstmp
            FROM (
                SELECT
                    ed.osm_id, ed.name, ed.name_ga, ed.name_en, ed.alt_name, ed.alt_name_ga,
                    ed.osm_user, ed.osm_timestamp, ed.attribution,
                    c.name as co_name, c.osm_id AS co_osm_id,
                    concat('http://www.townlands.ie/', ed.url_path) AS t_ie_url,
                    ST_SetSRID(ST_GeomFromGeoJSON(irish_townlands_polygon.polygon_geojson), 4326) AS geom
                FROM
                    irish_townlands_electoraldivision AS ed
                        JOIN irish_townlands_polygon ON (ed._polygon_geojson_id = irish_townlands_polygon.id)
                    LEFT OUTER JOIN irish_townlands_county AS c
                        ON (ed.county_id = c.id)
            ) AS xx
        """)

        townland_touching(directory, dbuser, dbpass)
