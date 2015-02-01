# encoding: utf-8
from __future__ import division

from django.db import models
from django.db.models import Sum, Q
from django.template.defaultfilters import slugify
from django.utils.translation import ungettext, ugettext
from django.utils.html import format_html
from django.core.urlresolvers import reverse
from django.conf import settings
import math

from django.db import models


def err_msg(msg, *args, **kwargs):
    msg = msg.format(*args, **kwargs)
    Error.objects.create(message=msg)
    print msg


class Metadata(models.Model):
    key = models.CharField(unique=True, db_index=True, max_length=50)
    value = models.CharField(max_length=255)

class Area(models.Model):

    class Meta:
        abstract = True

    osm_id = models.IntegerField()
    name = models.CharField(max_length=255, db_index=True)
    name_en = models.CharField(max_length=255, default=None, null=True, db_index=True)
    name_ga = models.CharField(max_length=255, default=None, null=True, db_index=True)
    alt_name = models.CharField(max_length=255, default=None, null=True, db_index=True)
    alt_name_ga = models.CharField(max_length=255, default=None, null=True, db_index=True)
    place = models.CharField(max_length=255, default=None, null=True)
    area_m2 = models.FloatField(db_index=True)
    water_area_m2 = models.FloatField(blank=True, null=True)
    url_path = models.CharField(db_index=True, max_length=255)
    unique_suffix = models.PositiveSmallIntegerField(null=True)

    centre_x = models.FloatField(default=0)
    centre_y = models.FloatField(default=0)

    bbox_width = models.FloatField(default=0)
    bbox_height = models.FloatField(default=0)

    polygon_geojson = models.TextField(default='')

    # When v1 was made. NULL means we don't know it yet
    osm_user = models.CharField(max_length=100, db_index=True, null=True)
    osm_uid = models.IntegerField(null=True)
    osm_timestamp = models.DateTimeField(db_index=True, null=True)

    def __unicode__(self):
        return "{0} ({1})".format(self.name, self.osm_id)

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
        acres_float = self.area_acres
        acres = int(acres_float)
        subacres = acres_float - acres

        roods = int(subacres * 4)
        perches = int((subacres * 4 - roods) * 40)

        return (acres, roods, perches)

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
        lat, lon = abs(self.centre_y), abs(self.centre_x)

        return u"{0[0]}° {0[1]}' {0[2]}\" N, {1[0]}° {1[1]}' {1[2]}\" W".format(float_to_sexagesimal(lat), float_to_sexagesimal(lon))

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
    def townland_cover_excl_water(self):
        townland_cover = self.townlands.aggregate(Sum('area_m2'))['area_m2__sum'] or 0
        return min((townland_cover / self.area_excl_water_m2) * 100.0, 100.0)

    @property
    def barony_cover(self):
        cover = self.baronies.aggregate(Sum('area_m2'))['area_m2__sum'] or 0
        return min((cover / self.area_m2) * 100.0, 100.0)

    @property
    def civil_parish_cover(self):
        cover = self.civil_parishes.aggregate(Sum('area_m2'))['area_m2__sum'] or 0
        return min((cover / self.area_m2) * 100.0, 100.0)

    @property
    def ed_cover(self):
        cover = self.eds.aggregate(Sum('area_m2'))['area_m2__sum'] or 0
        return min((cover / self.area_m2) * 100.0, 100.0)

    @property
    def townlands_sorted(self):
        return self.townlands.prefetch_related('county', 'barony', 'civil_parish').only("name", 'name_ga', 'alt_name', 'area_m2', 'url_path', 'county__name', 'barony__name', 'civil_parish__name').order_by('name')

    @property
    def baronies_sorted(self):
        return self.baronies.prefetch_related("townlands").order_by("name")

    @property
    def civil_parishes_sorted(self):
        return self.civil_parishes.prefetch_related("townlands").order_by("name")

    @property
    def eds_sorted(self):
        return self.eds.prefetch_related("townlands").order_by("name")

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
    def long_desc(self):
        name = self.name

        if self.name_ga:
            if self.alt_name_ga:
                name_ga = format_html(u" (<i>{0}</i> or <i>{1}</i>) ", self.name_ga, self.alt_name_ga)
            else:
                name_ga = format_html(u" (<i>{0}</i>) ", self.name_ga)
        else:
            name_ga = ''

        if self.alt_name:
            alt_name = format_html(u" (aka {0}) ", self.alt_name)
        else:
            alt_name = ''
            
        if getattr(self, 'civil_parish', None):
            civil_parish_name = ", " + ugettext("%(civil_parish_name)s Civil Parish") % {'civil_parish_name': self.civil_parish.name}
        else:
            civil_parish_name = ''

        if getattr(self, 'barony', None):
            barony_name = ", " + ugettext("Barony of %(barony_name)s") % {'barony_name': self.barony.name}
        else:
            barony_name = ''

        if getattr(self, 'county', None):
            county_name = ", " + ugettext("Co. %(county_name)s") % {'county_name': self.county.name}
        else:
            county_name = ''

        if self.place == 'island':
            island = ' ' + ugettext("(Island)") + ' '
        else:
            island = ''

        return format_html(
            u'<a href="{url_path}">{name}</a>{name_ga}{alt_name}{island}{civil_parish_name}{barony_name}{county_name}',
            url_path=reverse('view_area', args=[self.url_path]),
            name=self.name, name_ga=name_ga, alt_name=alt_name, island=island,
            civil_parish_name=civil_parish_name,
            barony_name=barony_name, county_name=county_name
        )

    @property
    def short_desc(self):
        return format_html(
            u'<a href="{url_path}">{name}</a>',
            url_path=settings.BASE_URL + reverse('view_area', args=[self.url_path]), name=self.name
        )


    @property
    def osm_type(self):
        return 'relation' if self.osm_id < 0 else 'way'

    @property
    def barony_list_textual(self):
        baronies = [b.short_desc for b in self.baronies_sorted]
        and_text = ugettext("and")
        if len(baronies) < 2:
            return "".join(baronies)
        else:
            return ", ".join(baronies[:-1]) + " " + and_text + " " + baronies[-1]


def float_to_sexagesimal(x):
    x = abs(x)
    deg = int(x)
    min = int((x - deg) * 60)
    sec = int((x - deg - (min/60.0))*3600)
    return (deg, min, sec)

class Barony(Area):
    county = models.ForeignKey("County", null=True, db_index=True, default=None, related_name="baronies")

    def generate_url_path(self):
        name = slugify(self.name.lower())
        if self.county:
            self.url_path = "{0}/{1}".format(self.county.name.lower(), name)
        else:
            self.url_path = "{0}".format(name)

        if self.unique_suffix:
            self.url_path += str(self.unique_suffix)

    def calculate_county(self):
        # This logic breaks if baronies cross county borders.
        counties = list(County.objects.defer("polygon_geojson").filter(townlands__barony=self).distinct())
        if len(counties) == 0:
            err_msg("Barony {barony} has no county", barony=self)
            return
        if len(counties) > 1:
            err_msg("Barony {barony} overlaps counties: {counties}", barony=self, counties=", ".join(x.name for x in counties))
            return
        self.county = counties[0]



class CivilParish(Area):
    county = models.ForeignKey("County", null=True, db_index=True, default=None, related_name="civil_parishes")

    def generate_url_path(self):
        name = slugify(self.name.lower())
        if self.county:
            self.url_path = "{0}/{1}".format(self.county.name.lower(), name)
        else:
            self.url_path = "{0}".format(name)

        if self.unique_suffix:
            self.url_path += str(self.unique_suffix)

    def calculate_county(self):
        # This logic breaks if CPs cross county borders.
        counties = list(County.objects.defer("polygon_geojson").filter(townlands__civil_parish=self).distinct())
        if len(counties) == 0:
            err_msg("Civil Parish {0} has no county", self)
            return
        if len(counties) > 1:
            err_msg("Civil Parish {cp} overlaps counties: {counties}", cp=self, counties=", ".join(x.name for x in counties))
            return
        self.county = counties[0]

    @property
    def baronies(self):
        """The baronies that this CP is in (might overlap)"""
        return Barony.objects.filter(townlands__in=self.townlands.all()).distinct().order_by("name")


class County(Area):

    polygon_townland_gaps = models.TextField(default='')
    polygon_townland_overlaps = models.TextField(default='')

    polygon_barony_gaps = models.TextField(default='')
    polygon_barony_overlaps = models.TextField(default='')

    polygon_civil_parish_gaps = models.TextField(default='')
    polygon_civil_parish_overlaps = models.TextField(default='')

    def is_name(self, other_name):
        return other_name.lower() in [self.name.lower(), 'county '+self.name.lower(), 'county london' + self.name.lower()]


    def generate_url_path(self):
        name = slugify(self.name.lower())
        self.url_path = "{0}".format(name)


class ElectoralDivision(Area):
    county = models.ForeignKey("County", null=True, db_index=True, default=None, related_name="eds")

    def generate_url_path(self):
        name = slugify(self.name.lower())
        if self.county:
            self.url_path = "{0}/{1}".format(self.county.name.lower(), name)
        else:
            self.url_path = "{0}".format(name)

        if self.unique_suffix:
            self.url_path += str(self.unique_suffix)

    def calculate_county(self):
        # This logic breaks if EDs cross county borders.
        counties = list(County.objects.defer("polygon_geojson").filter(townlands__ed=self).distinct())
        if len(counties) == 0:
            err_msg("ED {0} has no county", self)
            return
        if len(counties) > 1:
            err_msg("ED {ed} overlaps counties: {counties}", ed=self, counties=", ".join(x.name for x in counties))
            return
        self.county = counties[0]

    def baronies(self):
        """The baronies that this ED is in (might overlap)"""
        return Barony.objects.filter(townlands__in=self.townlands.all()).distinct().order_by("name")


class Townland(Area):
    county = models.ForeignKey(County, related_name='townlands', null=True, db_index=True)
    barony = models.ForeignKey(Barony, related_name='townlands', null=True)
    civil_parish = models.ForeignKey(CivilParish, related_name='townlands', null=True)
    ed = models.ForeignKey(ElectoralDivision, related_name='townlands', null=True)

    def generate_url_path(self):
        name = slugify(self.name.lower())
        def _pathify(*args):
            return "/".join(slugify(x.name.lower()) for x in args)

        if self.county and self.barony and self.civil_parish and self.ed:
            self.url_path = _pathify(self.county, self.barony, self.civil_parish, self.ed, self)
        elif self.county and self.barony and self.civil_parish:
            self.url_path = _pathify(self.county, self.barony, self.civil_parish, self)
        elif self.county and self.barony:
            self.url_path = _pathify(self.county, self.barony, self)
        elif self.county and self.civil_parish:
            self.url_path = _pathify(self.county, self.civil_parish, self)
        elif self.county:
            self.url_path = _pathify(self.county, self)
        else:
            self.url_path = "{0}".format(name)

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
