import csv, logging

import iso8601
import osm_find_first

from django.core.management.base import BaseCommand, CommandError

from irish_townlands.models import Townland, ElectoralDivision, CivilParish, Barony, County, Subtownland

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
        results = [clean_result_row(x) for x in known_data]

        results = {(x['osm_type'], x['osm_id']): x for x in results}
        
        # See if the file has details for OSM obj that aren't saved on the object.
        to_save = []
        to_look_up = []
        for klass in (Townland, ElectoralDivision, CivilParish, Barony, County, Subtownland):
            missing = klass.objects.filter(osm_timestamp__isnull=True).only("osm_id")
            for miss in missing:
                osm_history = results.get((miss.osm_type, abs(miss.osm_id)), None)
                if osm_history is not None:
                    miss.osm_user = osm_history['osm_user']
                    miss.osm_uid = osm_history['osm_uid']
                    miss.osm_timestamp = osm_history['osm_timestamp']
                    to_save.append(miss)
                else:
                    to_look_up.append(miss)

        # If we have added some details to some objects, save them now.
        logger.info("Saving %d objects.", len(to_save))
        for obj_to_save in to_save:
            obj_to_save.save()
        to_save = []

        # Construct the data structure of things we want to look up
        to_look_up_dict = [{'osm_type': x.osm_type, 'osm_id': abs(x.osm_id)} for x in to_look_up]


        # this is where we query the OSM API
        # doing the OSM query!
        logger.info("Querying OSM API for %d objects", len(to_look_up_dict))
        new_known_data = osm_find_first.find_first_from_csvs(csv_filename, to_look_up_dict)

        results = [clean_result_row(x) for x in new_known_data]
        results = {(x['osm_type'], x['osm_id']): x for x in results}

        for miss in to_look_up:
            osm_history = results.get((miss.osm_type, abs(miss.osm_id)), None)
            if osm_history is not None:
                logger.info("Found it %s", results[(miss.osm_type, abs(miss.osm_id))])
                miss.osm_user = osm_history['osm_user']
                miss.osm_uid = osm_history['osm_uid']
                miss.osm_timestamp = osm_history['osm_timestamp']
                to_save.append(miss)
            else:
                logger.error("Still have no data for %r", miss)
        
        logger.info("Saving %d objects.", len(to_save))
        for obj_to_save in to_save:
            obj_to_save.save()

