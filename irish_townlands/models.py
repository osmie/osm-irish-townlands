# encoding: utf-8
from __future__ import division

from django.db import models
from django.db.models import Sum, Q
from django.template.defaultfilters import slugify
from django.utils.translation import ungettext, ugettext
from django.utils.html import format_html, mark_safe
from django.core.urlresolvers import reverse
from django.conf import settings
import math

from django.db import models


from .utils import m2_to_arp, remove_prefixes, remove_accents

def err_msg(msg, *args, **kwargs):
    msg = msg.format(*args, **kwargs)
    Error.objects.create(message=msg)
    print msg

def pathify(*args):
    return "/".join(slugify(x.lower()) for x in args if x is not None)


def location_pretty(x, y):
    lat, lon = abs(y), abs(x)

    return u"{0[0]}° {0[1]}' {0[2]}\" N, {1[0]}° {1[1]}' {1[2]}\" W".format(float_to_sexagesimal(lat), float_to_sexagesimal(lon))

def float_to_sexagesimal(x):
    x = abs(x)
    deg = int(x)
    min = int((x - deg) * 60)
    sec = int((x - deg - (min/60.0))*3600)
    return (deg, min, sec)

def join_names_by_and(names):
    and_text = ugettext("and")
    if len(names) < 2:
        return "".join(names)
    else:
        return ", ".join(names[:-1]) + " " + and_text + " " + names[-1]

def alt_values_textual(value):
    """
    If the value of a tag has semicolons (;) to indicate alternative values,
    then split that out and join them together by and.
    e.g. turn 'a;b;c' into 'a, b and c'
    """
    splits = value.split(";")
    splits = [x.strip() for x in splits]
    return join_names_by_and(splits)

class Metadata(models.Model):
    key = models.CharField(unique=True, db_index=True, max_length=50)
    value = models.CharField(max_length=255)

class NameableThing(object):

    @property
    def osm_browse_url(self):
        return "http://www.openstreetmap.org/{type}/{id}".format(type=self.osm_type, id=abs(self.osm_id))

    @property
    def edit_in_josm_url(self):
        return "http://localhost:8111/import?url=http://api.openstreetmap.org/api/0.6/{type}/{id}/full".format(type=self.osm_type, id=abs(self.osm_id))

    @property
    def edit_in_potlatch_url(self):
        return "http://www.openstreetmap.org/edit?editor=potlatch2&{type}={id}".format(type=self.osm_type, id=abs(self.osm_id))

    @property
    def edit_in_id_url(self):
        return "http://www.openstreetmap.org/edit?editor=id&{type}={id}".format(type=self.osm_type, id=abs(self.osm_id))

    @property
    def edit_in_level0_url(self):
        return "http://level0.osmz.ru/?url={type}/{id}".format(type=self.osm_type, id=abs(self.osm_id))

    def full_name(self, incl_other_names=True, incl_hierachies=True, incl_misc=True):
        name = self.name

        name_ga = ''
        alt_name = ''
        if incl_other_names:
            if self.name_ga:
                if self.alt_name_ga:
                    name_ga = format_html(u" (<i>{0}</i> or <i>{1}</i>) ", self.name_ga, self.alt_name_ga_textual)
                else:
                    name_ga = format_html(u" (<i>{0}</i>) ", self.name_ga)

            if self.alt_name:
                alt_name = format_html(u" (aka {0}) ", self.alt_name_textual)
            
        townland_name = ''
        civil_parish_name = ''
        barony_name = ''
        county_name = ''
        if incl_hierachies:
            if getattr(self, 'townland', None):
                # for sub townlands
                townland_name = ", " + ugettext("%(townland_name)s Townland") % {'townland_name': self.townland.name }

            if getattr(self, 'civil_parish', None):
                civil_parish_name = ", " + ugettext("%(name)s Civil Parish") % {'name': self.civil_parish.name}

            if getattr(self, 'barony', None):
                barony_name = ", " + ugettext("Barony of %(barony_name)s") % {'barony_name': self.barony.name}

            if getattr(self, 'county', None):
                county_name = ", " + ugettext("Co. %(county_name)s") % {'county_name': self.county.name}

        island = ''
        census_name = ''
        if incl_misc:
            if self.place == 'island':
                island = ' ' + ugettext("(Island)") + ' '

            if self.has_different_name_census1901 or self.has_different_name_census1911:
                census_names = []
                if self.has_different_name_census1901: 
                    census_names.append(ugettext("'%(name)s' in 1901 Census") % { "name": self.name_census1901 })
                if self.has_different_name_census1911: 
                    census_names.append(ugettext("'%(name)s' in 1911 Census") % { "name": self.name_census1911 })
                census_name = ' (' + ', '.join(census_names) + ')'



        return format_html(
            u'<a href="{url_path}">{name}</a>{name_ga}{alt_name}{island}{census_name}{townland_name}{civil_parish_name}{barony_name}{county_name}',
            url_path=reverse('view_area', args=[self.url_path]),
            name=self.name, name_ga=name_ga, alt_name=alt_name, island=island,
            townland_name=townland_name, civil_parish_name=civil_parish_name,
            barony_name=barony_name, county_name=county_name,
            census_name=census_name
        )

    @property
    def short_desc(self):
        return self.full_name(incl_other_names=False, incl_hierachies=False, incl_misc=False)

    @property
    def medium_desc(self):
        return self.full_name(incl_other_names=True, incl_hierachies=False, incl_misc=True)

    @property
    def long_desc(self):
        return self.full_name(incl_other_names=True, incl_hierachies=True, incl_misc=True)


    @property
    def osm_type(self):
        return 'relation' if self.osm_id < 0 else 'way'

class Polygon(models.Model):
    osm_id = models.IntegerField()
    polygon_geojson = models.TextField(default='')

class Area(models.Model, NameableThing):

    class Meta:
        abstract = True

    osm_id = models.IntegerField(unique=True)

    # The name tag
    name_tag = models.CharField(max_length=255, db_index=True)
    name_en = models.CharField(max_length=255, default=None, null=True, db_index=True)
    name_ga = models.CharField(max_length=255, default=None, null=True, db_index=True)

    name_census1901_tag = models.CharField(max_length=255, default=None, null=True, db_index=True)
    name_census1911_tag = models.CharField(max_length=255, default=None, null=True, db_index=True)

    alt_name = models.CharField(max_length=255, default=None, null=True, db_index=True)
    alt_name_ga = models.CharField(max_length=255, default=None, null=True, db_index=True)

    official_name_en = models.CharField(max_length=255, default=None, null=True, db_index=True)
    official_name_ga = models.CharField(max_length=255, default=None, null=True, db_index=True)

    place = models.CharField(max_length=255, default=None, null=True)
    area_m2 = models.FloatField(db_index=True)
    water_area_m2 = models.FloatField(blank=True, null=True)
    url_path = models.CharField(db_index=True, max_length=255)
    unique_suffix = models.PositiveSmallIntegerField(null=True)
    source = models.CharField(max_length=255, default=None, null=True)
    attribution = models.CharField(max_length=255, default=None, null=True)
    ref = models.CharField(max_length=255, db_index=True, null=True, default=None)

    centre_x = models.FloatField(default=0)
    centre_y = models.FloatField(default=0)

    bbox_width = models.FloatField(default=0)
    bbox_height = models.FloatField(default=0)

    _polygon_geojson = models.ForeignKey(Polygon, default=None, null=True)

    # When v1 was made. NULL means we don't know it yet
    osm_user = models.CharField(max_length=100, db_index=True, null=True)
    osm_uid = models.IntegerField(null=True)
    osm_timestamp = models.DateTimeField(db_index=True, null=True)

    logainm_ref = models.CharField(max_length=255, default=None, null=True, db_index=True)

    def __unicode__(self):
        return "{0} ({1})".format(self.name, self.osm_id)

    @property
    def name(self):
        return self.name_tag

    @property
    def polygon_geojson(self):
        return self._polygon_geojson.polygon_geojson

    @property
    def area_km2(self):
        return self.area_m2 / 1000000

    @property
    def area_acres(self):
        # intacres
        return self.area_m2 / 4046.8564

        # usacres
        #return self.area * 0.00024710439

    @property
    def area_hectares(self):
        return self.area_km2 * 100

    @property
    def area_acres_roods_perches(self):
        return m2_to_arp(self.area_m2)

    @property
    def area_acres_roods_perches_textual(self):
        acres, roods, perches = self.area_acres_roods_perches
        return ", ".join([
            (ungettext("%d acre", "%d acres", acres) % acres),
            (ungettext("%d rood", "%d roods", roods) % roods),
            (ungettext("%d perch", "%d perches", perches) % perches),
        ])

    @property
    def area_mile2(self):
        return self.area_m2 / 2589988.1


    def __unicode__(self):
        return self.name

    @property
    def centre_pretty(self):
        return location_pretty(x=self.centre_x, y=self.centre_y)

    @property
    def area_excl_water_m2(self):
        # Some things don't have water calculated and stored. e.g. CPs.
        # cf. https://github.com/rory/osm-irish-townlands/issues/51
        return self.area_m2 - (self.water_area_m2 or 0)

    @property
    def water_percent(self):
        return ( self.water_area_m2 / self.area_m2 ) * 100

    @property
    def townland_cover(self):
        return self.townland_cover_excl_water

    @property
    def townland_cover_incl_water(self):
        townland_cover = self.townlands.aggregate(Sum('area_m2'))['area_m2__sum'] or 0
        return min((townland_cover / self.area_m2) * 100.0, 100.0)

    @property
    def townland_area(self):
        return self.townlands.aggregate(Sum('area_m2'))['area_m2__sum'] or 0

    @property
    def townland_cover_excl_water(self):
        return min((self.townland_area / self.area_excl_water_m2) * 100.0, 100.0)

    @property
    def barony_area(self):
        return self.baronies.aggregate(Sum('area_m2'))['area_m2__sum'] or 0

    @property
    def barony_cover(self):
        return min((self.barony_area / self.area_m2) * 100.0, 100.0)

    @property
    def civil_parish_area(self):
        return self.civil_parishes.aggregate(Sum('area_m2'))['area_m2__sum'] or 0

    @property
    def civil_parish_cover(self):
        return min((self.civil_parish_area / self.area_m2) * 100.0, 100.0)

    @property
    def ed_area(self):
        return self.eds.aggregate(Sum('area_m2'))['area_m2__sum'] or 0

    @property
    def ed_cover(self):
        return min((self.ed_area / self.area_m2) * 100.0, 100.0)

    @property
    def townlands_sorted(self):
        return self.townlands.prefetch_related('county', 'barony', 'civil_parish').only("name_tag", 'name_ga', 'alt_name', 'alt_name_ga', 'area_m2', 'url_path', 'county__name', 'barony__name', 'civil_parish__name', "place").order_by("name_tag")

    @property
    def baronies_sorted(self):
        return self.baronies.only("name_tag", "url_path", "county__name").order_by("name_tag")

    @property
    def counties_sorted(self):
        return self.counties.only("name_tag", "url_path").order_by("name_tag")

    @property
    def civil_parishes_sorted(self):
        return self.civil_parishes.only("name_tag", "url_path").order_by("name_tag")

    @property
    def eds_sorted(self):
        return self.eds.only("name_tag", "url_path", "county__id").order_by("name_tag")


    @property
    def barony_list_textual(self):
        baronies = [b.short_desc for b in self.baronies_sorted]
        return join_names_by_and(baronies)

    @property
    def counties_list_textual(self):
        counties = [b.short_desc for b in self.counties_sorted]
        return join_names_by_and(counties)


    @property
    def county_name(self):
        # This is a bit of hack to do "select name from county where id = $COUNTY_ID"
        try:
            return County.objects.filter(id=self.county_id).values("name_tag")[0]["name_tag"]
        except:
            return None

    def expand_to_alternatives(self, incl_irish=True, desc="long"):
        assert desc in ["long", "medium", "short"]

        # List of tuples. Each tuple has the key to use for sorting, and then
        # the html content to use for that entry.
        results = []

        # What description do we use for this item?
        if desc == 'long':
            this_desc = self.long_desc
        elif desc == 'medium':
            this_desc = self.medium_desc
        elif desc == 'short':
            this_desc = self.short_desc
        else:
            raise NotImplementedError()

        # An area called "Foo or Bar" should be expanded to 2 entries, "Foo"
        # and "Bar". This code split it that way.
        def split_string(input_string):
            strings_to_split = [" and ", " or ", " agus ", u" nó ", ";"]
            results = []
            for s in strings_to_split:
                if s in input_string:
                    names = input_string.split(s)
                    for name in names[1:]:
                        results.append(name)
            return results

        # Given a name, convert it to sortable key
        def name_to_key(name):
            key = remove_prefixes(name, ['An t-', 'An t', 'An ', 'Na h-', 'Na h', 'Na '])
            key = remove_accents(key)
            key = key.lower()
            return key

        # First: We always include the "name" as is.
        arp_text = ugettext("Area in Acres, Rods and Perches")
        arp = self.area_acres_roods_perches
        results.append((
            name_to_key(self.name),
            format_html(u'{} <abbr title="{}">{} A, {} R, {} P</abbr>',
                mark_safe(unicode(this_desc)), arp_text, arp[0], arp[1], arp[2])))

        # Then look for alternatives
        alternatives = []

        # Include "Bar" part of "Foo or Bar"
        alternatives.extend(split_string(self.name))

        # Include alt_name, even if alt_name is "Foo or Bar"
        if self.alt_name:
            alternatives.append(self.alt_name)
            alternatives.extend(split_string(self.alt_name))

        # Different names in the census
        if self.name_census1901_tag:
            alternatives.append(self.name_census1901_tag)
            alternatives.extend(split_string(self.name_census1901_tag))
        if self.name_census1911_tag:
            alternatives.append(self.name_census1911_tag)
            alternatives.extend(split_string(self.name_census1911_tag))

        
        # Optional Irish name(s)
        if incl_irish:
            if self.name_ga:
                alternatives.append(self.name_ga)
                alternatives.extend(split_string(self.name_ga))

            if self.alt_name_ga:
                alternatives.append(self.alt_name_ga)
                alternatives.extend(split_string(self.alt_name_ga))

        # Construct HTML 
        for alt in alternatives:
            key = name_to_key(alt)

            results.append((key, format_html(u"{} <i>(see {})</i>".format(unicode(alt), this_desc))))

        return results

    @property
    def townlands_for_list_display(self):
        """
        Returns a list of strings that can be used to show a list of townlands.
        A townland can be entered more than once if there's an altname, namega,
        altnamega, or an " or " or an " and " in the name.

        It's then sorted by a sensible key for manual searching.
        """

        townlands = self.townlands_sorted
        results = []

        for t in townlands:
            results.extend(t.expand_to_alternatives())

        results.sort()
        results = [x[1] for x in results]
        return results

    def added_order(self):
        klass = self.__class__
        num_older = klass.objects.filter(Q(osm_timestamp__lt=self.osm_timestamp) | (Q(osm_timestamp=self.osm_timestamp) & Q(name__lt=self.name))).count()
        return num_older + 1

    @property
    def subtownlands(self):
        return Subtownland.objects.filter(townland__county=self)

    @property
    def subtownlands_sorted(self):
        return self.subtownlands.prefetch_related('townland__county', 'townland__barony', 'townland__civil_parish', 'townland').only("name_tag", 'name_ga', 'url_path', 'townland__county__name', 'townland__barony__name', 'townland__civil_parish__name', "townland__name").order_by("name_tag")

    @property
    def county_name(self):
        """Return string of the county's name. Returns None if there is no county for this object. if there is more than one county, it returns an arbitary county"""
        raise NotImplementedError()

    @property
    def name_census1901(self):
        """What name should we search for when searching a 1901 census"""
        return self.name_census1901_tag if self.has_different_name_census1901 else self.name

    @property
    def name_census1901_display(self):
        """For a 1901 census search, returns current name if unchanged, else shows both names"""
        if self.has_different_name_census1901:
            return "{} ({})".format(self.name_census1901, self.name)
        else:
            return self.name

    @property
    def name_census1911(self):
        """What name should we search for when searching a 1911 census"""
        return self.name_census1911_tag if self.has_different_name_census1911 else self.name

    @property
    def name_census1911_display(self):
        """For a 1911 census search, returns current name if unchanged, else shows both names"""
        if self.has_different_name_census1911:
            return "{} ({})".format(self.name_census1911, self.name)
        else:
            return self.name

    @property
    def has_different_name_census1901(self):
        return self.name_census1901_tag is not None and self.name_census1901_tag != self.name

    @property
    def has_different_name_census1911(self):
        return self.name_census1911_tag is not None and self.name_census1911_tag != self.name

    @property
    def alt_name_textual(self):
        return alt_values_textual(self.alt_name)

    @property
    def alt_name_ga_textual(self):
        return alt_values_textual(self.alt_name_ga)

    @property
    def alt_name_textual(self):
        return alt_values_textual(self.alt_name)

    @property
    def ed_name_census1911(self):
        try:
            return self.ed.name_census1911
        except:
            return ''

    @property
    def ed_name_census1901(self):
        try:
            return self.ed.name_census1901
        except:
            return ''

class Barony(Area):
    county = models.ForeignKey("County", null=True, db_index=True, default=None, related_name="baronies")

    def generate_url_path(self):
        name = slugify(self.name.lower())
        county_name = self.county_name

        self.url_path = pathify(county_name, name)

        if self.unique_suffix:
            self.url_path += str(self.unique_suffix)

    def calculate_county(self):
        # This logic breaks if baronies cross county borders.
        counties = list(County.objects.filter(townlands__barony=self).distinct())
        if len(counties) == 0:
            err_msg("Barony {barony} has no county", barony=self)
            return
        if len(counties) > 1:
            err_msg("Barony {barony} overlaps counties: {counties}", barony=self, counties=", ".join(x.name for x in counties))
            return
        self.county = counties[0]

    @property
    def county_name(self):
        counties = list(County.objects.filter(townlands__barony=self).values_list("name_tag", flat=True).distinct())
        if len(counties) == 0:
            return None
        else:
            return counties[0]

    @property
    def civil_parishes(self):
        return CivilParish.objects.filter(townlands__in=self.townlands.all()).distinct().order_by("name_tag")



class CivilParish(Area):
    counties = models.ManyToManyField("County", null=True, db_index=True, default=None, related_name="civil_parishes")

    def generate_url_path(self):
        name = slugify(self.name.lower())
        county_name = self.county_name
        self.url_path = pathify(county_name, name)

        if self.unique_suffix:
            self.url_path += str(self.unique_suffix)

    def calculate_county(self):
        counties = list(County.objects.filter(townlands__civil_parish=self).distinct())
        for county in counties:
            self.counties.add(county)

    @property
    def baronies(self):
        """The baronies that this CP is in (might overlap)"""
        return Barony.objects.filter(townlands__in=self.townlands.all()).distinct().order_by("name_tag")

    @property
    def county_name(self):
        counties = list(County.objects.filter(townlands__civil_parish=self).values_list("name_tag", flat=True).distinct())
        if len(counties) == 0:
            return None
        else:
            return counties[0]

    @property
    def crosses_county_border(self):
        return self.counties.count() > 1

    @property
    def county(self):
        """
        If this CP is in exactly one county, then return that one.
        When calculating long_desc, it does getattr(cp, 'county', None). This
        change means that for the vast majority of single-county CPs, they will
        be displayed with a county name, which is better.
        """
        counties = self.counties.all()
        if len(counties) == 1:
            return counties[0]
        else:
            return 0

    @property
    def barony(self):
        """
        If this CP is in exactly one barony, then return that one.
        Similar to county property
        When calculating long_desc, it does getattr(cp, 'county', None). This
        change means that for the vast majority of single-county CPs, they will
        be displayed with a county name, which is better.
        """
        baronies = self.baronies.all()
        if len(baronies) == 1:
            return baronies[0]
        else:
            return 0



class County(Area):

    polygon_townland_gaps = models.TextField(default='', null=True)
    polygon_townland_overlaps = models.TextField(default='', null=True)

    polygon_barony_gaps = models.TextField(default='', null=True)
    polygon_barony_overlaps = models.TextField(default='', null=True)

    polygon_civil_parish_gaps = models.TextField(default='', null=True)
    polygon_civil_parish_overlaps = models.TextField(default='', null=True)

    polygon_ed_gaps = models.TextField(default='', null=True)
    polygon_ed_overlaps = models.TextField(default='', null=True)

    def is_name(self, other_name):
        return other_name.lower() in [self.name.lower(), 'county '+self.name.lower(), 'county london' + self.name.lower()]

    def generate_url_path(self):
        name = slugify(self.name.lower())
        self.url_path = "{0}".format(name)

    @property
    def county_name(self):
        return self.name


class ElectoralDivision(Area):
    county = models.ForeignKey("County", null=True, db_index=True, default=None, related_name="eds")

    def generate_url_path(self):
        name = slugify(self.name.lower())
        county_name = self.county_name

        self.url_path = pathify(county_name, name)

        if self.unique_suffix:
            self.url_path += str(self.unique_suffix)

    def calculate_county(self):
        # This logic breaks if EDs cross county borders.
        counties = list(County.objects.filter(townlands__ed=self).distinct())
        if len(counties) == 0:
            err_msg("ED {0} has no county", self)
            return
        if len(counties) > 1:
            err_msg("ED {ed} overlaps counties: {counties}", ed=self, counties=", ".join(x.name for x in counties))
            return
        self.county = counties[0]

    def baronies(self):
        """The baronies that this ED is in (might overlap)"""
        return Barony.objects.filter(townlands__in=self.townlands.all()).distinct().order_by("name_tag")

    @property
    def county_name(self):
        counties = list(County.objects.filter(townlands__ed=self).values_list("name_tag", flat=True).distinct())
        if len(counties) == 0:
            return None
        else:
            return counties[0]


class Townland(Area):
    county = models.ForeignKey(County, related_name='townlands', null=True, db_index=True)
    barony = models.ForeignKey(Barony, related_name='townlands', null=True)
    civil_parish = models.ForeignKey(CivilParish, related_name='townlands', null=True)
    ed = models.ForeignKey(ElectoralDivision, related_name='townlands', null=True)

    def generate_url_path(self):
        name = slugify(self.name.lower())

	county_name = County.objects.filter(id=self.county_id).values_list("name_tag", flat=True)[0] if self.county_id else None
	civil_parish_name = CivilParish.objects.filter(id=self.civil_parish_id).values_list("name_tag", flat=True)[0] if self.civil_parish_id else None
	barony_name = Barony.objects.filter(id=self.barony_id).values_list("name_tag", flat=True)[0] if self.barony_id else None
	ed_name = ElectoralDivision.objects.filter(id=self.ed_id).values_list("name_tag", flat=True)[0] if self.ed_id else None

        self.url_path = pathify(county_name, barony_name, civil_parish_name, ed_name, name)

        if self.unique_suffix:
            self.url_path += str(self.unique_suffix)


    @property
    def area_rank(self):
        larger = Townland.objects.filter(area_m2__gt=self.area_m2).count()
        rank = larger + 1
        return rank

    @property
    def area_rank_county(self):
        assert self.county
        larger = Townland.objects.filter(county=self.county, area_m2__gt=self.area_m2).count()
        rank = larger + 1
        return rank

    @property
    def touching_townlands(self):
        return self.touching_as_a.order_by("townland_b__name")

    @property
    def county_name(self):
        counties = list(County.objects.filter(townlands__townland=self).values_list("name_tag", flat=True).distinct())
        if len(counties) == 0:
            return None
        else:
            return counties[0]

class TownlandTouch(models.Model):
    class Meta:
        unique_together = [('townland_a', 'townland_b')]
    townland_a = models.ForeignKey(Townland, related_name="touching_as_a")
    townland_b = models.ForeignKey(Townland, related_name="touching_as_b")
    length_m = models.FloatField(default=0)
    direction_radians = models.FloatField()

    @property
    def direction_words(self):
        degrees = math.degrees(self.direction_radians) % 360
        if 45 < degrees <= 135:
            return "east"
        elif 135 < degrees <= 225:
            return "south"
        elif 225 < degrees <= 315:
            return "west"
        else:
            return "north"

class Error(models.Model):
    message = models.TextField()


class Progress(models.Model):
    when = models.DateField(auto_now=True)
    percent = models.FloatField()
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return u"{name} was at {percent} on {when}".format(name=self.name, percent=self.percent, when=self.when)

class Subtownland(models.Model, NameableThing):
    osm_id = models.CharField(max_length=50, unique=True)
    osm_user = models.CharField(max_length=100, db_index=True, null=True)
    osm_uid = models.IntegerField(null=True)
    osm_timestamp = models.DateTimeField(db_index=True, null=True)

    url_path = models.CharField(db_index=True, max_length=255)
    unique_suffix = models.PositiveSmallIntegerField(null=True)

    name_tag = models.CharField(max_length=255, db_index=True)
    name_ga = models.CharField(max_length=255, default=None, null=True, db_index=True)
    alt_name = models.CharField(max_length=255, db_index=True, null=True)

    location_x = models.FloatField(default=0)
    location_y = models.FloatField(default=0)

    townland = models.ForeignKey(Townland, related_name='subtownlands')

    # Some hacks so that long_desc and search will work.
    alt_name_ga = models.CharField(max_length=255, default=None, null=True, db_index=True)
    name_census1901_tag = models.CharField(max_length=255, default=None, null=True, db_index=True)
    name_census1911_tag = models.CharField(max_length=255, default=None, null=True, db_index=True)

    logainm_ref = models.CharField(max_length=255, default=None, null=True, db_index=True)

    place = None
    has_different_name_census1901 = False
    has_different_name_census1911 = False

    @property
    def name(self):
        return self.name_tag

    @property
    def county(self):
        return self.townland.county if self.townland else None

    @property
    def barony(self):
        return self.townland.barony if self.townland else None

    @property
    def civil_parish(self):
        return self.townland.civil_parish if self.townland else None

    @property
    def ed(self):
        return self.townland.ed if self.townland else None

    def generate_url_path(self):
        name = slugify(self.name.lower())

        if self.townland:

	    county_name = County.objects.filter(id=self.townland.county_id).values_list("name_tag", flat=True)[0] if self.townland.county_id else None
	    civil_parish_name = CivilParish.objects.filter(id=self.townland.civil_parish_id).values_list("name_tag", flat=True)[0] if self.townland.civil_parish_id else None
	    barony_name = Barony.objects.filter(id=self.townland.barony_id).values_list("name_tag", flat=True)[0] if self.townland.barony_id else None
	    ed_name = ElectoralDivision.objects.filter(id=self.townland.ed_id).values_list("name_tag", flat=True)[0] if self.townland.ed_id else None

            self.url_path = pathify(county_name, barony_name, civil_parish_name, ed_name, self.townland.name, name)

        else:
            self.url_path = "{0}".format(name)

        if self.unique_suffix:
            self.url_path += str(self.unique_suffix)

    @property
    def centre_pretty(self):
        return location_pretty(x=self.location_x, y=self.location_y)

    @property
    def osm_type(self):
        return "node"

    def __unicode__(self):
        return "{0} ({1})".format(self.name, self.osm_id)
