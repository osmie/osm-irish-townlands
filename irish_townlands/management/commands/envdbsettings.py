import os
from django.conf import settings

from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    help = 'eval the output of this to put the database username and password in the environment'

    def handle_noargs(self, **options):
        self.stdout.write("TOWNLANDS_DB_USER={} TOWNLANDS_DB_PASS={}".format(settings.DATABASES['default']['USER'], settings.DATABASES['default']['PASSWORD']))

