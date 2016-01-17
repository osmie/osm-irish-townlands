from django.conf import settings
import os, os.path
from django.db import connection
from irish_townlands.models import Townland
import django.template.loader

from django.core.management.base import BaseCommand, CommandError

from irish_townlands.models import Townland, ElectoralDivision, CivilParish, Barony, County, Subtownland

def logainm_id_to_path(lid):
    s = "{:06d}".format(int(lid))
    return ("{}/{}".format(s[0:2], s[2:4]), "{}.png".format(s[4:6]))

def get_existing_logainm_ids():
    results = set()
    for klass in [ County, Barony, CivilParish, ElectoralDivision, Townland]:
        for lid in klass.objects.exclude(logainm_ref=None).values_list('logainm_ref', flat=True):
            lids = lid.split(";")
            results.update(lids)

    return results

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--icons-directory")

    def handle(self, *args, **options):
        directory = options['icons_directory']
        existing_logainm_ids = get_existing_logainm_ids()
        yes_icon = os.path.join(directory, "green_check.png")
        no_icon = os.path.join(directory, "red_cross.png")

        for logainm_id in range(1, 119001):
            logainm_id = str(logainm_id)

            icon_dir, icon_name = logainm_id_to_path(logainm_id)
            icon_dir = os.path.join(directory, icon_dir)
            icon_filename = os.path.join(icon_dir, icon_name)

            if not os.path.exists(icon_dir):
                os.makedirs(icon_dir)

            if os.path.exists(icon_filename):
                os.remove(icon_filename)

            if logainm_id in existing_logainm_ids:
                icon = yes_icon
            else:
                icon = no_icon

            os.symlink(icon, icon_filename)
