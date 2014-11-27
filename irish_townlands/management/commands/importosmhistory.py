import csv, logging

import iso8601
import osm_find_first

from django.core.management.base import BaseCommand, CommandError

#from irish_townlands.lib import importosmhistory
from irish_townlands.models import Townland, ElectoralDivision, CivilParish, Barony

logger = logging.getLogger(__name__)

def clean_result_row(result):
    result['osm_id'] = int(result['osm_id'])
    result['osm_timestamp'] = iso8601.parse_date(result['osm_timestamp'])
    return result

class Command(BaseCommand):
    def handle(self, *args, **options):
        csv_filename = args[0]

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        logger.setLevel(logging.DEBUG)

        with open(csv_filename) as fp:
            csv_reader = csv.DictReader(fp)

            known_data = list(csv_reader)

        # Now make it indexable
        # TODO convert datetime string to datetime obj
        results = [clean_result_row(x) for x in known_data]

        results = {(x['osm_type'], x['osm_id']): x for x in results}
        
        to_save = []
        to_look_up = []
        for klass in (Townland, ElectoralDivision, CivilParish, Barony):
            missing = klass.objects.filter(osm_timestamp__isnull=True)
            for miss in missing:
                osm_history = results.get((miss.osm_type, abs(miss.osm_id)), None)
                if osm_history is not None:
                    miss.osm_user = osm_history['osm_user']
                    miss.osm_uid = osm_history['osm_uid']
                    miss.osm_timestamp = osm_history['osm_timestamp']
                    to_save.append(miss)
                else:
                    to_look_up.append(miss)

        logger.info("Saving %d objects.", len(to_save))
        for obj_to_save in to_save:
            obj_to_save.save()

        to_look_up_dict = [{'osm_type': x.osm_type, 'osm_id': abs(x.osm_id)} for x in to_look_up]


        # this is where we query the OSM API
        # doing the OSM query!
        #import pudb ; pudb.set_trace()
        logger.info("Querying OSM API for %d objects", len(to_look_up_dict))
        new_known_data = osm_find_first.find_first_from_csvs(csv_filename, to_look_up_dict)

        # save it for later
        #osm_find_first.write_to_csv(csv_filename, to_look_up_dict)

        results = [clean_result_row(x) for x in new_known_data]
        results = {(x['osm_type'], x['osm_id']): x for x in results}

        for obj in to_look_up:
            osm_history = results.get((miss.osm_type, abs(miss.osm_id)), None)
            if osm_history is not None:
                logger.info("Found it %s", results[(miss.osm_type, abs(miss.osm_id))])
                miss.osm_user = osm_history['osm_user']
                miss.osm_uid = osm_history['osm_uid']
                miss.osm_timestamp = osm_history['osm_timestamp']
                to_save.append(miss)
            else:
                logger.error("Still have no data for %s", obj)
        
        logger.info("Saving %d objects.", len(to_save))
        for obj_to_save in to_save:
            obj_to_save.save()

