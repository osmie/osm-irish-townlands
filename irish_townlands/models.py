# encoding: utf-8

from django.db import models
from django.db.models import Sum, Q
from django.template.defaultfilters import slugify
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
    name_ga = models.CharField(max_length=255, default=None, null=True)
    alt_name = models.CharField(max_length=255, default=None, null=True)
    area_m2 = models.FloatField(db_index=True)
    water_area_m2 = models.FloatField(blank=True, null=True)
    url_path = models.CharField(db_index=True, max_length=255)
    unique_suffix = models.PositiveSmallIntegerField(null=True)

    centre_x = models.FloatField(default=0)
    centre_y = models.FloatField(default=0)

    bbox_width = models.FloatField(default=0)
    bbox_height = models.FloatField(default=0)

    polygon_geojson = models.TextField(default='')

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
    def area_mile2(self):
        return self.area_m2 / 2589988.1


    def __unicode__(self):
        return self.name

    @property
    def centre_pretty(self):
        lat, lon = abs(self.centre_y), abs(self.centre_x)

        return u"{0[0]}° {0[1]}' {0[2]}\" N, {1[0]}° {1[1]}' {1[2]}\" W".format(float_to_sexagesimal(lat), float_to_sexagesimal(lon))

    @property
    def townland_cover(self):
        townland_cover = self.townlands.aggregate(Sum('area_m2'))['area_m2__sum'] or 0
        return (townland_cover / self.area_m2) * 100.0

    @property
    def barony_cover(self):
        cover = self.baronies.aggregate(Sum('area_m2'))['area_m2__sum'] or 0
        return (cover / self.area_m2) * 100.0

    @property
    def civil_parish_cover(self):
        cover = self.civil_parishes.aggregate(Sum('area_m2'))['area_m2__sum'] or 0
        return (cover / self.area_m2) * 100.0

    @property
    def townlands_sorted(self):
        return self.townlands.prefetch_related("barony", "civil_parish").order_by("name")

    @property
    def baronies_sorted(self):
        return self.baronies.prefetch_related("townlands").order_by("name")

    @property
    def civil_parishes_sorted(self):
        return self.civil_parishes.prefetch_related("townlands").order_by("name")

    @property
    def osm_browse_url(self):
        return "http://www.openstreetmap.org/browse/{type}/{id}".format(type=('relation' if self.osm_id < 0 else 'way'), id=abs(self.osm_id))

    @property
    def edit_in_josm_url(self):
        return "http://localhost:8111/import?url=http://api.openstreetmap.org/api/0.6/{type}/{id}/full".format(type=('relation' if self.osm_id <0 else 'way'), id=abs(self.osm_id))

    @property
    def edit_in_potlatch_url(self):
        return "http://www.openstreetmap.org/edit?editor=potlatch2&{type}={id}".format(type=('relation' if self.osm_id < 0 else 'way'), id=abs(self.osm_id))


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
        counties = list(County.objects.filter(townlands__barony=self).distinct())
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
        self.url_path = "{0}".format(name)

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
        counties = list(County.objects.filter(townlands__civil_parish=self).distinct())
        if len(counties) == 0:
            err_msg("Civil Parish {0} has no county", self)
            return
        if len(counties) > 1:
            err_msg("Civil Parish {cp} overlaps counties: {counties}", cp=self, counties=", ".join(x.name for x in counties))
            return
        self.county = counties[0]

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


class Townland(Area):
    county = models.ForeignKey(County, related_name='townlands', null=True, db_index=True)
    barony = models.ForeignKey(Barony, related_name='townlands', null=True)
    civil_parish = models.ForeignKey(CivilParish, related_name='townlands', null=True)

    def generate_url_path(self):
        name = slugify(self.name.lower())
        def _pathify(*args):
            return "/".join(slugify(x.name.lower()) for x in args)

        if self.county and self.barony and self.civil_parish:
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
