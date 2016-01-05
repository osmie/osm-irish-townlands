from django.conf import settings
import subprocess
import os, os.path
import csv
import psycopg2
from django.db import connection
from irish_townlands.models import Townland
import django.template.loader
import hashlib
import colorsys
import random

from django.core.management.base import BaseCommand, CommandError

def colour_for_user(username):
    random.seed(username)
    hue = random.random()
    rgb = colorsys.hls_to_rgb(hue, 0.66, 1)
    rgb = [int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255)]
    rgb_string = "#{:x}{:x}{:x}".format(*rgb)

    return rgb_string

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--write-mapnik-to")
        parser.add_argument("--shapefile")

    def handle(self, *args, **options):
        shapefile = options['shapefile']
        output_file = options['write_mapnik_to']

        # create shapefile
        subprocess.call(["pgsql2shp", "-f", shapefile, "townlands", "select osm_user, (st_dump(geom)).geom as geom from  (select osm_user, st_union(way) as geom from irish_townlands_townland join valid_polygon using (osm_id) group by osm_user) as t;"], stdout=subprocess.PIPE)

        # Create mapnik template
        users = list(Townland.objects.values_list("osm_user", flat=True).distinct())
        usercolours = [(user.replace("'", "\\'"), colour_for_user(user)) for user in users]
        new_template = django.template.loader.get_template("irish_townlands/townlanduser.xml").render({'usercolours': usercolours, 'shapefile': shapefile})

        with open(output_file, 'w') as fp:
            fp.write(new_template)

