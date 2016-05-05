"""
Management command to conver the OSM imported data in your postgis database to
the django models.
"""
from __future__ import division

from optparse import make_option

from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.conf import settings
from django.db.models import Sum
from django import db
from ...models import County, Townland, Barony, CivilParish, ElectoralDivision, TownlandTouch, Metadata, Error, Progress, Subtownland, Polygon, NameEntry

from collections import defaultdict
import psycopg2
from contextlib import contextmanager
import datetime, time
import subprocess
import resource

DEBUG = False

def curr_mem_usage():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage[2]*resource.getpagesize() / (1024 * 1024)

@contextmanager
def printer(msg):
    """Context statement to print when a task starts & ends."""
    start = time.time()
    old_mem = curr_mem_usage()
    if DEBUG:
        print "Starting {} (curr mem {:.1f}MB)".format(msg, old_mem)
    yield
    duration = time.time() - start
    new_mem = curr_mem_usage()
    delta_mem = new_mem - old_mem
    if DEBUG:
        print "Finished "+msg+" in {:.1f} sec with {:.1f}MB delta memory (curr mem {:.1f}MB)".format(duration, delta_mem, new_mem)

    # We always want to do this
    db.reset_queries()


def err_msg(msg, *args, **kwargs):
    """Log an error message to DB & print it. """
    msg = msg.format(*args, **kwargs)
    Error.objects.create(message=msg)


def rm_suffix(obj, attr, bad_suffix):
    string = getattr(obj, attr)
    if string.lower().endswith(bad_suffix.lower()):
        string = string[:-len(bad_suffix)]
        setattr(obj, attr, string)
        
def rm_prefix(obj, attr, bad_suffix):
    string = getattr(obj, attr)
    if string.lower().startswith(bad_suffix.lower()):
        string = string[len(bad_suffix):]
        setattr(obj, attr, string)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--verbose',
            action='store_true',
            dest='verbose',
            default=False,
            help='Be verbose, and print debugging output'),
        make_option('--quick',
            action='store_true',
            dest='quick',
            default=False,
            help='Skip some of the timeconsuming tasks'),
        )


    def delete_all_data(self):
        # Deletes all existing data.
        #
        # NB: It's important that it's "DELETE FROM" not "TRUNCATE". When
        # "TRUNCATE" is used, then this transaction will get a ACCESS EXCLUSIVE
        # lock on the table (which is all tables, since we need to delete all
        # tables). This means no other transaction will be able to read from
        # the data (even read old data?) until after this transaction has
        # finished (and the ACCESS EXCLUSIVE lock is released). This means that
        # while an import is in process, townlands.ie is down. Which sucks. It
        # also brings down a log of other sites on the same host, since the
        # apache workers are tied up waiting for the lock to released. By using
        # "DELETE" instead, this doesn't happen.
        #
        # cf. http://www.postgresql.org/docs/9.4/static/explicit-locking.html
        django_cursor = connection.cursor()
        for model in [ Townland, CivilParish, County, Barony, ElectoralDivision, Subtownland, Polygon, TownlandTouch, NameEntry ]:
            table = model._meta.db_table
            # Doing a raw SQL rather than model.objects.all().delete() because
            # this uses less memory
            django_cursor.execute("DELETE FROM {table} CASCADE".format(table=table))

        # Some extra things to delete
        for table in ['irish_townlands_civilparish_counties']:
            django_cursor.execute("DELETE FROM {table} CASCADE".format(table=table))

        # Clear errors
        Error.objects.all().delete()


    def connect_to_db(self):
        # using postgres (we presume)
        dbuser, dbpass = settings.DATABASES['default']['USER'], settings.DATABASES['default']['PASSWORD']
        dbname = settings.DATABASES['default']['NAME']
        self.conn = psycopg2.connect(host='127.0.0.1', database=dbname, user=dbuser, password=dbpass)

        self.cursor = self.conn.cursor()

    def create_area_obj(self, name, where_clause, django_model, cols):
        """Create one type of area."""
        results = {}

        table = django_model._meta.db_table
        polygon_table = Polygon._meta.db_table

        with printer("getting " + name):
            self.cursor.execute("select {0} from valid_polygon where {1} ;".format(", ".join(c[0] for c in cols), where_clause))

            for row in self.cursor:
                kwargs = dict(zip([c[1] for c in cols], row))
                new_obj = django_model(**kwargs)
                new_obj.save()

            # Update the geojson separately to save memory
            django_cursor = connection.cursor()
            django_cursor.execute("insert into {polygon_table} (osm_id, polygon_geojson) select osm_id, ST_AsGeoJSON(geo) as geo from valid_polygon where {where}".format(polygon_table=polygon_table, where=where_clause))
            django_cursor.execute("update {table} set _polygon_geojson_id = p_id from (select t.id as t_id, p.id as p_id from {table} as t join {polygon_table} as p using (osm_id) where t._polygon_geojson_id IS NULL) as tt where id = t_id".format(table=table, polygon_table=polygon_table))

            results = dict((x.osm_id, x) for x in django_model.objects.only("osm_id", "name_tag").all())

        return results

    def calculate_touching_townlands(self):
        # adding townlandtouches is a lot of a SQL. Django keeps these queries
        # around afterwards, which is a lot of strings to store, which causes
        # the memory to increase. reset_queries clears this. django usually
        # calls this after every HTTP request, but we don't have HTTP requests
        # here
        # touching
        bucket_size = 10

        touching_townlands = []
        with printer("touching townlands"):
            # Sometimes st_intersection(a.geo, b.geo) causes a topology
            # exception, but st_intersection(a.way, b.way)::geography doesn't. 
            self.cursor.execute("select a.osm_id, b.osm_id, ST_length(st_intersection(a.way, b.way)::geography), ST_Azimuth(st_centroid(a.way), st_centroid(st_intersection(a.way, b.way))) from valid_polygon as a inner join valid_polygon as b on st_touches(a.way, b.way) where a.admin_level = '10' and b.admin_level = '10' and a.osm_id <> b.osm_id;")
            for idx, (a_osm_id, b_osm_id, length_m, direction_radians) in enumerate(self.cursor):
                touching_townlands.append(TownlandTouch(townland_a=self.townlands[a_osm_id], townland_b=self.townlands[b_osm_id], length_m=length_m, direction_radians=direction_radians))
                if len(touching_townlands) >= bucket_size:
                    TownlandTouch.objects.bulk_create(touching_townlands)
                    touching_townlands = []
                    db.reset_queries()

            # save anything left
            TownlandTouch.objects.bulk_create(touching_townlands)
            db.reset_queries()


    def water_area_m2_in_county(self, original_county_name):
        self.cursor.execute("""
            select sum(
               case
                 when st_within(water_polygon.way, valid_polygon.way) then ST_Area(water_polygon.geo)
                 else ST_Area(ST_Intersection(valid_polygon.geo, water_polygon.geo))
               end) as water_area_m2
            from valid_polygon inner join water_polygon ON ST_Intersects(valid_polygon.way, water_polygon.way)
            where valid_polygon.admin_level  = '6' and name = '{original_county_name}'
        """.format(original_county_name=original_county_name))
        water_area_m2 = list(self.cursor)
        assert len(water_area_m2) == 1
        water_area_m2 = water_area_m2[0][0] or 0
        return water_area_m2

    def calculate_counties(self):
        with printer("creating counties"):

            county_names = set([
                "Tyrone", "Kerry", "Dublin", "Down", "Fermanagh", "Wexford", "Mayo", "Carlow",
                "Wicklow", "Longford", "Westmeath", "Cork", "Leitrim", "Laois", "Waterford", "Tipperary",
                "Monaghan", "Kilkenny", "Galway", "Meath", "Donegal", "Cavan", "Kildare", "Offaly",
                "Derry", "Clare", "Armagh", "Antrim", "Limerick", "Louth", "Sligo", "Roscommon",
                ])

            self.counties = self.create_area_obj('counties', "admin_level = '6'", County, self.cols)

            for c in self.counties.values():
                original_county_name = c.name_tag

                # sanitize name
                rm_prefix(c, 'name_tag', 'County ')
                rm_prefix(c, 'name_ga', 'Contae  ')
                if c.name_tag == 'Londonderry':
                    c.name_tag = u'Derry'

                # calculate amount of water in this county
                with printer("getting water are for county {}".format(c.name)):
                    water_area_m2 = self.water_area_m2_in_county(original_county_name)
                c.water_area_m2 = water_area_m2
                if c.water_area_m2 >= c.area_m2:
                    err_msg("County {0}, too much water?", c.name)

                c.save()

                if not any(c.is_name(county_name) for county_name in county_names):
                    print "Deleting dud county ", c.name
                    del self.counties[c.osm_id]
                    c.delete()
                else:
                    c.generate_url_path()
                    c.save()

            seen_counties = set(c.name for c in self.counties.values())
            missing_counties = county_names - seen_counties
            for missing in missing_counties:
                err_msg("Could not find County {0}. Is the county boundary/relation broken?", missing)

    def calculate_subtownlands(self):
        with printer("Calculating subtownlands"):
            self.cursor.execute("select distinct on (s.osm_id) s.osm_id, s.name, s.\"name:ga\", alt_name, st_x(st_transform(s.way, 4326)) as x, st_y(st_transform(s.way, 4326)) as y, t.osm_id as townland_id from planet_osm_point as s join valid_polygon as t on (st_within(s.way, t.way)) where s.place = 'locality' and s.locality = 'subtownland' and t.admin_level = '10';")
            subtownlands = []
            for osm_id, name, name_ga, alt_name, location_x, location_y, townland_id in self.cursor:
                subtownlands.append(Subtownland(osm_id=osm_id, name_tag=name, name_ga=name_ga, alt_name=alt_name, location_x=location_x, location_y=location_y, townland=self.townlands[townland_id]))
            Subtownland.objects.bulk_create(subtownlands)
            
            return {s.osm_id: s for s in Subtownland.objects.all()}


    def clean_cp_names(self):
        # remove "Civil Parish" suffix from C.P.s
        for cp in self.civil_parishes.values():
            rm_suffix(cp, 'name_tag', ' Civil Parish')

    def clean_barony_names(self):
        # remove "Barony of" suffix from baronies
        for b in self.baronies.values():
            rm_prefix(b, 'name_tag', 'Barony of ')
            rm_suffix(b, 'name_tag', ' Barony')

    def clean_ed_names(self):
        # remove "ED" suffix from EDs
        for ed in self.eds.values():
            rm_suffix(ed, 'name_tag', ' ED')
            rm_suffix(ed, 'name_tag', ' DED')

    def calculate_townlands_in_counties(self):
        with printer("townlands in counties"):
            self.cursor.execute("""
                select c.name, t.osm_id
                from valid_polygon as c
                    join valid_polygon as t
                    on (c.admin_level = '6' and t.admin_level = '10' and st_contains(c.way, t.way));
            """)

            for county_name, townland_osm_id in self.cursor:
                county = [c for c in self.counties.values() if c.is_name(county_name)]

                if len(county) == 0:
                    err_msg("Unknown county {0}", county_name)
                else:
                    if len(county) > 1:
                        err_msg("Townland (OSM ID: {townland_osm_id}) is in >1 counties! Overlapping border? Counties: {counties}", townland_osm_id=townland_osm_id, counties=", ".join(county))
                        break
                    county = county[0]
                    if townland_osm_id not in self.townlands:
                        err_msg("Weird townland ids")
                        break
                    townland = self.townlands[townland_osm_id]
                    if townland.county not in [None, county]:
                        err_msg("Townland {townland} is in 2 counties! Overlapping border? First county: {townland.county}, Second county: {county}", townland=townland, county=county)
                    else:
                        townland.county = county




    def calculate_townlands_in_baronies(self):
        with printer("townlands in baronies"):
            self.cursor.execute("select b.osm_id, t.osm_id from valid_polygon as b join valid_polygon as t on (b.boundary = 'barony' and t.admin_level = '10' and st_contains(b.way, t.way));")

            for barony_osm_id, townland_osm_id in self.cursor:
                if not ( self.townlands[townland_osm_id].barony is None or self.townlands[townland_osm_id].barony.osm_id == barony_osm_id ):
                    err_msg("Overlapping Baronies")
                else:
                    self.townlands[townland_osm_id].barony = self.baronies[barony_osm_id]
                    self.townlands[townland_osm_id].save()

    def calculate_townlands_in_civil_parishes(self):
        with printer("townlands in civil parishes"):
            self.cursor.execute("select b.osm_id, t.osm_id from valid_polygon as b join valid_polygon as t on (b.boundary = 'civil_parish' and t.admin_level = '10' and st_contains(b.way, t.way));")

            for cp_osm_id, townland_osm_id in self.cursor:
                townland = self.townlands[townland_osm_id]
                other_cp = self.civil_parishes[cp_osm_id]
                if not ( townland.civil_parish is None or townland.civil_parish.osm_id == cp_osm_id ):
                    err_msg("County {county}, Townland {td} is in civil parish {cp1} and {cp2}. Overlapping Civil Parishes?", td=townland, cp1=townland.civil_parish, cp2=other_cp, county=townland.county)
                else:
                    self.townlands[townland_osm_id].civil_parish = self.civil_parishes[cp_osm_id]
                    self.townlands[townland_osm_id].save()

    def calculate_townlands_in_eds(self):
        with printer("townlands in EDs"):
            self.cursor.execute("select e.osm_id, t.osm_id from valid_polygon as e join valid_polygon as t on (e.admin_level = '9' and t.admin_level = '10' and st_contains(e.way, t.way));")

            for ed_osm_id, townland_osm_id in self.cursor:
                townland = self.townlands[townland_osm_id]
                other_ed = self.eds[ed_osm_id]
                if not ( townland.ed is None or townland.ed.osm_id == ed_osm_id ):
                    err_msg("County {county}, Townland {td} is in ED {ed1} and {ed2}. Overlapping EDs?", td=townland, ed1=townland.ed, ed2=other_ed, county=townland.county)
                else:
                    self.townlands[townland_osm_id].ed = self.eds[ed_osm_id]
                    self.townlands[townland_osm_id].save()


    def calculate_baronies_in_counties(self):
        for barony in self.baronies.values():
            barony.calculate_county()

    def calculate_civil_parishes_in_counties(self):
        for civil_parish in self.civil_parishes.values():
            if civil_parish.townlands.count() == 0:
                err_msg("No townlands in Civil Parish {0}".format(civil_parish.name))
            else:
                civil_parish.calculate_county()

    def calculate_eds_in_counties(self):
        with printer("eds in counties"):
            self.cursor.execute("""
                select c.name, e.osm_id
                from valid_polygon as c
                    join valid_polygon as e
                    on (c.admin_level = '6' and e.admin_level = '9' and st_contains(c.way, e.way));
            """)

            for county_name, ed_osm_id in self.cursor:
                county = [c for c in self.counties.values() if c.is_name(county_name)]

                if len(county) == 0:
                    err_msg("Unknown county {0}", county_name)
                else:
                    if len(county) > 1:
                        err_msg("ED (OSM ID: {ed_osm_id}) is in >1 counties! Overlapping border? Counties: {counties}", ed_osm_id=ed_osm_id, counties=", ".join(county))
                        break
                    county = county[0]
                    if ed_osm_id not in self.eds:
                        err_msg("Weird ed ids")
                        break
                    ed = self.eds[ed_osm_id]
                    if ed.county not in [None, county]:
                        err_msg("ED {ed} is in 2 counties! Overlapping border? First county: {ed.county}, Second county: {county}", ed=ed,county=county)
                    else:
                        ed.county = county



    def calculate_gaps_and_overlaps(self, table, osm_id, sub_ids):
        # gap
        sql = """update {table} set polygon_townland_gaps = (select st_AsGeoJSON(st_transform(
                    st_difference(county.way, all_townlands.way)
                    , 4326)::geography)
                from (select way from valid_polygon where osm_id = {osm_id}) as county, (select st_union(way) as way from valid_polygon where osm_id in ({sub_osm_ids}) ) as all_townlands) as tt where osm_id = {osm_id};""".format(osm_id=county_osm_id, sub_osm_ids=",".join(sub_ids), table=table)
        self.cursor.execute(sql)

        # overlap
        sql = """select
                    st_AsGeoJSON(st_geographyfromtext(st_astext(st_transform(
                        st_union(st_intersection(st_difference(a.way, st_boundary(a.way)), st_difference(b.way, st_boundary(b.way))))
                    , 4326))))
            from (select osm_id, way from valid_polygon where osm_id in ({sub_osm_ids})) as a, (select osm_id, way from valid_polygon where osm_id in ({sub_osm_ids})) as b where a.osm_id <> b.osm_id and st_overlaps(a.way, b.way);""".format(sub_osm_ids=",".join(sub_ids))
        self.cursor.execute(sql)
        details = list(self.cursor)
        assert len(details) == 1
        overlaps = details[0][0] or ''

        return gaps, overlaps

    def calculate_county_not_covered_for_ids(self, county, attr_name, ids):
        table = county._meta.db_table
        polygon_id = county._polygon_geojson_id
        polygon_table = Polygon._meta.db_table
        county_osm_id = county.osm_id
        django_cursor = connection.cursor()

        if len(ids) == 0:
            # Shortcut, there is townlands here
            django_cursor.execute("update {table} set polygon_{attr_name}_gaps = (select polygon_geojson from {polygon_table} where id = {polygon_id}) where osm_id={county_osm_id}".format(table=table, attr_name=attr_name, polygon_table=polygon_table, polygon_id=polygon_id, county_osm_id=county_osm_id))
            db.reset_queries()
            django_cursor.execute("update {table} set polygon_{attr_name}_overlaps = '';".format(table=table, attr_name=attr_name, polygon_table=polygon_table, polygon_id=polygon_id))
            db.reset_queries()
        else:
            with printer("Updating gaps for {name}".format(name=county.name)):
                sql = """update {table} set polygon_{attr_name}_gaps = (select st_AsGeoJSON(st_transform( st_difference(county.way, all_townlands.way) , 4326)::geography) from (select way from valid_polygon where osm_id = {county_osm_id}) as county, (select st_union(way) as way from valid_polygon where osm_id in ({sub_osm_ids})) as all_townlands) where osm_id = {county_osm_id};""".format(county_osm_id=county_osm_id, sub_osm_ids=",".join(ids), table=table, attr_name=attr_name)
                django_cursor.execute(sql)
                db.reset_queries()
            with printer("Updating overlaps for {name}".format(name=county.name)):
                # overlap
                sql = """
                update {table} set polygon_{attr_name}_overlaps = (
                  select
                    coalesce(st_AsGeoJSON(st_transform(st_union(st_intersection(st_difference(a.way, st_boundary(a.way)), st_difference(b.way, st_boundary(b.way)))), 4326)::geography), '')
                    from (
                        select osm_id, way
                        from valid_polygon
                        where osm_id in ({sub_osm_ids})
                      ) as a,
                      (
                        select osm_id, way from valid_polygon where osm_id in ({sub_osm_ids})
                      ) as b
                      where
                        a.osm_id < b.osm_id
                        and st_overlaps(a.way, b.way)
                  )
                  where osm_id = {county_osm_id};""".format(sub_osm_ids=",".join(ids), county_osm_id=county_osm_id, table=table, attr_name=attr_name)
                django_cursor.execute(sql)
                db.reset_queries()


    def calculate_county_not_covered_for_where(self, county, attr_name, where):
        table = county._meta.db_table
        polygon_id = county._polygon_geojson_id
        polygon_table = Polygon._meta.db_table
        county_osm_id = county.osm_id
        django_cursor = connection.cursor()
        
        # gaps
        with printer("finding gaps for {name}".format(name=county.name)):
            sql = "update {table} set polygon_{attr_name}_gaps = (select st_AsGeoJSON(st_transform(st_difference(st_difference(county_way, townland_way), st_boundary(county_way)), 4326)) from (select county.way as county_way, st_union(townland.way) as townland_way from (select way from valid_polygon where osm_id = {county_osm_id}) as county join (select way from valid_polygon where {where}) as townland on (county.way && townland.way) group by county.way) as t) where osm_id = {county_osm_id}".format(
                county_osm_id=county_osm_id, where=where, attr_name=attr_name, table=table)
            try:
                django_cursor.execute(sql)
            except:
                pass
            db.reset_queries()

        # overlaps
        with printer("finding overlaps for {name}".format(name=county.name)):
            # overlap
            sql = """
            update {table} set polygon_{attr_name}_overlaps = (
                select st_AsGeoJSON(st_transform(st_union(st_intersection(townland1.way, townland2.way)), 4326)) from (select way from valid_polygon where osm_id = {county_osm_id}) as county join (select osm_id, way from valid_polygon where {where}) as townland1 on (county.way && townland1.way) join (select osm_id, way from valid_polygon where {where}) as townland2 on (st_overlaps(townland1.way, townland2.way) and townland1.osm_id < townland2.osm_id) )
                where osm_id = {county_osm_id}""".format(
                    county_osm_id=county_osm_id, table=table, attr_name=attr_name, where=where)
            try:
                django_cursor.execute(sql)
            except:
                pass
            db.reset_queries()


    def calculate_not_covered(self):
        # County level gaps in coverage of townlands
        with printer("finding land in county not covered by td/bar/cp"):
            for county in self.counties.values():
                with printer("finding land in county {} not covered by td/bar/cp".format(county.name)):
                    county_osm_id = county.osm_id
                    table = county._meta.db_table

                    with printer("finding land in county {} not covered by townlands".format(county.name)):
                        these_townlands = set(str(t.osm_id) for t in self.townlands.values() if t.county == county)
                        self.calculate_county_not_covered_for_where(county, 'townland', "admin_level = '10'")

                    with printer("finding land in county {} not covered by EDs".format(county.name)):
                        self.calculate_county_not_covered_for_where(county, 'ed', "admin_level = '9'")

                    with printer("finding land in county {} not covered by baronies".format(county.name)):
                        these_baronies = set(str(b.osm_id) for b in self.baronies.values() if b.county == county)
                        self.calculate_county_not_covered_for_where(county, 'barony', "boundary = 'barony'")

                    with printer("finding land in county {} not covered by civil parishes".format(county.name)):
                        these_civil_parishes = set(str(cp.osm_id) for cp in self.civil_parishes.values() if county in cp.counties.all())
                        self.calculate_county_not_covered_for_where(county, 'civil_parish', "boundary = 'civil_parish'")

                    county.save()


    def calculate_unique_urls(self):
        with printer("uniqifying townland urls"):
            all_areas = self.townlands.values() + self.civil_parishes.values() + self.baronies.values() + self.counties.values() + self.eds.values()
            all_points = self.subtownlands.values()

            for objs in [ all_areas, all_points ]:
                for x in objs:
                    x.generate_url_path()
                    db.reset_queries()

                overlapping_url_paths = defaultdict(set)
                for x in objs:
                    overlapping_url_paths[x.url_path].add(x)
                for url_path in overlapping_url_paths:
                    if len(overlapping_url_paths[url_path]) == 1:
                        continue
                    for x, i in zip(sorted(overlapping_url_paths[url_path], key=lambda x: getattr(x, 'area_m2', 0)), range(1, len(overlapping_url_paths[url_path])+1)):
                        x.unique_suffix = i
                        x.save()
                        x.generate_url_path()

                assert len(set(t.url_path for t in self.townlands.values())) == len(self.townlands)


    def calculate_name_entries(self):
        translation.active("en_IE")
        with printer("calculating name entries"):
            for name in ['townlands', 'baronies']:
                with printer("calculating {} name entries".format(name)):
                    for o in getattr(self, name).values():
                        for desc in ('short', 'medium', 'long'):
                            for sort_key, is_irish, display_html in o.expand_to_alternatives(desc):
                                NameEntry(desc=desc[0], is_irish=is_irish, sort_key=sort_key, display_html=display_html, area=o).save()



    def save_all_objects(self):
        # save all now
        with printer("final objects save"):
            for objs in [self.townlands, self.civil_parishes, self.baronies, self.counties, self.eds, self.subtownlands]:
                for x in objs.values():
                    x.save()
                    db.reset_queries()

    def record_progress(self):
        with printer("recording progress"):
            area_of_ireland = County.objects.all().aggregate(Sum('area_m2'))['area_m2__sum'] or 0
            area_of_all_townlands = Townland.objects.all().aggregate(Sum('area_m2'))['area_m2__sum'] or 0
            if area_of_ireland == 0:
                townland_progress = 0
            else:
                townland_progress = ( area_of_all_townlands / area_of_ireland ) * 100

            Progress.objects.create(percent=townland_progress, name="ireland-tds")

            for county in County.objects.only("id"):
                Progress.objects.create(percent=county.townland_cover, name=county.name+"-tds")


    def update_metadata(self):
        with printer("updating metadata"):
            last_updated, _ = Metadata.objects.get_or_create(key="lastupdate")
            last_updated.value = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
            last_updated.save()

            try:
                data_age, _ = Metadata.objects.get_or_create(key="dataage")
                #value = subprocess.check_output(['osmconvert', '--out-timestamp', '/home/rory/code/python/django-osm-irish-townlands/ireland-and-northern-ireland.osm.pbf'])
                value = subprocess.check_output(['/home/rory/osmconvert', '--out-timestamp', '/var/www/townlands/ireland-and-northern-ireland.osm.pbf'])
                data_age.value = value
                data_age.save()
            except:
                pass


    def handle(self, *args, **options):
        self.townlands = {}
        self.baronies = {}
        self.counties = {}
        self.civil_parishes = {}
        self.subtownlands = {}
        self.eds = {}

        if options['verbose']:
            global DEBUG
            DEBUG = True

        # delete old
        with transaction.atomic():

            with printer("deleting all old data"):
                self.delete_all_data()

            self.cols = [
                ('name', 'name_tag'),
                ('"name:ga"', 'name_ga'),
                ('"name:en"', 'name_en'),
                ('alt_name', 'alt_name'),
                ('"alt_name:ga"', 'alt_name_ga'),
                ('"official_name:en"', 'official_name_en'),
                ('"official_name:ga"', 'official_name_ga'),
                ('"logainm:ref"', 'logainm_ref'),
                ('"name:census1901"', 'name_census1901_tag'),
                ('"name:census1911"', 'name_census1911_tag'),
                ('"name:griffithsvaluation"', 'name_griffithsvaluation_tag'),
                ('osm_id', 'osm_id'),
                ('place', 'place'),
                ('"source"', 'source'),
                ('attribution', 'attribution'),
                ('ref', 'ref'),
                ('st_area(st_transform(way, 29902))', 'area_m2'),
                ('ST_X(st_transform((ST_centroid(way)), 4326))', 'centre_x'),
                ('ST_Y(st_transform((ST_centroid(way)), 4326))', 'centre_y'),
            ]

            self.connect_to_db()

            self.townlands = self.create_area_obj('townlands', "admin_level = '10'", Townland, self.cols)

            if not options['quick']:
                self.calculate_touching_townlands()

            self.calculate_counties()

            self.baronies = self.create_area_obj('baronies', "boundary = 'barony'", Barony, self.cols)
            self.civil_parishes = self.create_area_obj('civil parishes', "boundary = 'civil_parish'", CivilParish, self.cols)
            self.eds = self.create_area_obj('electoral_divisions', "admin_level = '9'", ElectoralDivision, self.cols)
            self.subtownlands = self.calculate_subtownlands()

            self.clean_cp_names()
            self.clean_barony_names()
            self.clean_ed_names()

            self.calculate_townlands_in_counties()
            self.calculate_townlands_in_baronies()
            self.calculate_townlands_in_civil_parishes()
            self.calculate_townlands_in_eds()
            self.calculate_baronies_in_counties()
            self.calculate_civil_parishes_in_counties()

            self.calculate_eds_in_counties()

            self.save_all_objects()

            if not options['quick']:
                self.calculate_not_covered()

            self.calculate_unique_urls()

            self.calculate_name_entries()

            self.save_all_objects()

            self.record_progress()

            self.update_metadata()
