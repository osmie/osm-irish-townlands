"""Views."""
from __future__ import division
import re
from datetime import timedelta, datetime, date
import math
import json
import urllib
from itertools import groupby
from collections import defaultdict

from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template.loader import render_to_string
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.db.models import Sum, Count, Q
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.utils import feedgenerator
from django.utils.translation import ungettext, ugettext
from django.utils.html import format_html, mark_safe

from .models import Metadata, Townland, CivilParish, Barony, County, ElectoralDivision, Error, Progress, Subtownland
from .pages import PAGES

COUNTIES = [u'Antrim', u'Armagh', u'Carlow', u'Cavan', u'Clare', u'Cork',
            u'Derry', u'Donegal', u'Down', u'Dublin', u'Fermanagh', u'Galway',
            u'Kerry', u'Kildare', u'Kilkenny', u'Laois', u'Leitrim',
            u'Limerick', u'Longford', u'Louth', u'Mayo', u'Meath', u'Monaghan',
            u'Offaly', u'Roscommon', u'Sligo', u'Tipperary', u'Tyrone',
            u'Waterford', u'Westmeath', u'Wexford', u'Wicklow']



def progress(request):
    last_update = get_last_update()
    counties = County.objects.order_by("name_tag").only("name_tag", "url_path").all()
    errors = Error.objects.all().values_list('message', flat=True)

    area_of_ireland_incl_water = County.objects.all().aggregate(Sum('area_m2'))['area_m2__sum'] or 0
    water_of_ireland = County.objects.all().aggregate(Sum('water_area_m2'))['water_area_m2__sum'] or 0
    area_of_ireland_excl_water = area_of_ireland_incl_water - water_of_ireland
    area_of_ireland = area_of_ireland_excl_water

    area_of_all_townlands = Townland.objects.all().aggregate(Sum('area_m2'))['area_m2__sum'] or 0
    area_of_all_eds = ElectoralDivision.objects.all().aggregate(Sum('area_m2'))['area_m2__sum'] or 0
    area_of_all_civil_parishes = CivilParish.objects.all().aggregate(Sum('area_m2'))['area_m2__sum'] or 0
    area_of_all_baronies = Barony.objects.all().aggregate(Sum('area_m2'))['area_m2__sum'] or 0

    if area_of_ireland == 0:
        townland_progress = civil_parish_progress = barony_progress = 0
    else:
        townland_progress = ( area_of_all_townlands / area_of_ireland ) * 100
        ed_progress = ( area_of_all_eds / area_of_ireland ) * 100
        civil_parish_progress = ( area_of_all_civil_parishes / area_of_ireland ) * 100
        barony_progress = ( area_of_all_baronies / area_of_ireland ) * 100

    groups = [
        ('NI', ['Antrim', 'Armagh', 'Derry', 'Down', 'Fermanagh', 'Tyrone']),
        ('ROI', [ u'Carlow', u'Cavan', u'Clare', u'Cork',
            u'Donegal', u'Dublin', u'Galway',
            u'Kerry', u'Kildare', u'Kilkenny', u'Laois', u'Leitrim',
            u'Limerick', u'Longford', u'Louth', u'Mayo', u'Meath', u'Monaghan',
            u'Offaly', u'Roscommon', u'Sligo', u'Tipperary',
            u'Waterford', u'Westmeath', u'Wexford', u'Wicklow'] ),
        ('Leinster', ["Carlow", "Dublin", "Kildare", "Kilkenny", "Laois", "Longford", "Louth", "Meath", "Offaly", "Westmeath", "Wexford", "Wicklow",]),
        ('Munster', ["Clare", "Cork", "Kerry", "Limerick", "Tipperary", "Waterford",]),
        ('Connaght', ["Galway", "Leitrim", "Mayo", "Roscommon", "Sligo"]),
        ('Ulster', ["Antrim", "Armagh", "Cavan", "Donegal", "Down", "Fermanagh", "Derry", "Monaghan", "Tyrone"]),
    ]
    group_details = []

    county_details = {name: {'townland_area': 0, 'area_m2': 0, 'barony_area': 0, 'ed_area': 0, 'civil_parish_area': 0} for name in COUNTIES}

    # populate counties
    county_details.update({
        county.name_tag: {
            'area_m2': county.area_m2,
            'area_excl_water_m2': county.area_excl_water_m2,
            'townland_area': county.townland_area,
            'ed_area': county.ed_area,
            'civil_parish_area': county.civil_parish_area,
            'barony_area': county.barony_area}
          for county in counties})


    for groupname, thesecounties in groups:
        group_details.append((groupname, {
            'townland_cover': (sum(county_details[name]['townland_area'] for name in thesecounties) / sum(county_details[name]['area_m2'] for name in thesecounties)) * 100.0,
            'barony_cover': (sum(county_details[name]['barony_area'] for name in thesecounties) / sum(county_details[name]['area_m2'] for name in thesecounties)) * 100.0,
            'civil_parish_cover': (sum(county_details[name]['civil_parish_area'] for name in thesecounties) / sum(county_details[name]['area_m2'] for name in thesecounties)) * 100.0,
            'ed_cover': (sum(county_details[name]['ed_area'] for name in thesecounties) / sum(county_details[name]['area_m2'] for name in thesecounties)) * 100.0,
        }))

    # Logainm data
    logainm = {}
    total_log = 0
    total_all = 0
    for key, klass in [ ('counties', County), ('baronies', Barony), ('civil_parishes', CivilParish), ('eds', ElectoralDivision), ('townlands', Townland)]:
        obj_all = klass.objects.all().count()
        has_log = klass.objects.exclude(logainm_ref=None).count()
        logainm[key+"_done"] = has_log
        logainm[key+"_all"] = obj_all
        logainm[key] = (float(has_log) * 100.0) / float(obj_all)
        total_all += obj_all
        total_log += has_log

    logainm['all'] = (float(total_log) * 100.0) / float(total_all)
    logainm['all_done'] = total_log
    logainm['all_all'] = total_all


    return render_to_response('irish_townlands/progress.html',
        {
            'counties':counties, 'last_update':last_update, 'errors':errors,
            'townland_progress': townland_progress, 'ed_progress': ed_progress,
            'civil_parish_progress': civil_parish_progress, 'barony_progress': barony_progress,
            'groups': group_details, 'logainm': logainm,
         },
        context_instance=RequestContext(request))


def duplicatenames(request):
    # Dupe names. Nothing wrong with duplicate names, it happens
    duplicate_townland_names = []
    duplicate_names = Townland.objects.all().values("name_tag").annotate(count=Count("name_tag")).filter(count__gte=2).order_by('-count', "name_tag")
    for item in duplicate_names:
        townland_name, townland_count = item["name_tag"], item['count']
        townlands = Townland.objects.filter(name_tag=townland_name).order_by("county__name_tag", "barony__name_tag", "civil_parish__name_tag").values('url_path', 'county__name_tag', 'barony__name_tag', 'civil_parish__name_tag')
        duplicate_townland_names.append({"name_tag": townland_name, 'count': townland_count, 'townlands': townlands})

    return render_to_response('irish_townlands/duplicatenames.html',
        {
            'duplicate_townland_names': duplicate_townland_names,
         },
        context_instance=RequestContext(request))

def get_last_update():
    try:
        last_update = int(Metadata.objects.get(key="lastupdate").value)
        last_update = datetime(1970, 1, 1) + timedelta(seconds=last_update)
    except Exception:
        last_update = "N/A"

    try:
        data_age = Metadata.objects.get(key="dataage").value
    except Exception:
        data_age = "N/A"

    return (last_update, data_age)

def county_debug(request, url_path):
    last_update = get_last_update()
    # strip debug from url to get county
    url_path = re.sub('debug/$', '', url_path)

    # County debug page
    try:
        x = County.objects.select_related().get(url_path=url_path)
    except:
        # Couldn't find county
        raise Http404("County not found")

    return render_to_response('irish_townlands/countydebug_detail.html', {'county': x, 'last_update': last_update}, context_instance=RequestContext(request))

def view_area(request, url_path=None):
    last_update = get_last_update()

    # County index page
    if url_path in ['all', None]:
        return render_to_response('irish_townlands/index.html', {
            'counties': County.objects.only('name_tag', 'url_path').order_by('name_tag').all(),
            'num_baronies': Barony.objects.all().count(),
            'num_civil_parishes': CivilParish.objects.all().count(),
            'num_eds': ElectoralDivision.objects.all().count(),
            'num_townlands': Townland.objects.all().count(),
            'last_update': last_update,
            }, context_instance=RequestContext(request))

    # Detail pages
    # County
    try:
        name = "county"
        x = County.objects.only("name_tag", "url_path", "area_m2", "water_area_m2", "osm_user", "osm_timestamp", "osm_id").select_related().get(url_path=url_path)
        return render_to_response('irish_townlands/'+name+'_detail.html', {name: x, name+"_name": x.name, 'last_update': last_update}, context_instance=RequestContext(request))
    except County.DoesNotExist:
        pass

    for model, name in (
                (Townland, 'townland'), (CivilParish, 'civil_parish'),
                (Barony, 'barony'), (ElectoralDivision, 'ed'), (Subtownland, 'subtownland') ):
        try:
            x = model.objects.select_related().get(url_path=url_path)
            return render_to_response('irish_townlands/'+name+'_detail.html', {name: x, name+"_name": x.name, 'last_update': last_update}, context_instance=RequestContext(request))
        except model.DoesNotExist:
            continue  #  on to next model

    # nothing by here?
    # Do a search!
    search_url = reverse('search') + "?" + urllib.urlencode({'q': url_path})
    return redirect(search_url)

def days_to_string(days):
    days = int(days)
    years, days = divmod(days, 365)
    months, days = divmod(days, 30)
    weeks, days = divmod(days, 7)
    output = ""
    if years > 0:
        output += ungettext("%d year", "%d years", years) % years
    if months > 0:
        output += " " + ungettext("%d month", "%d months", months) % months
    if weeks > 0:
        output += " " + ungettext("%d week", "%d weeks", weeks) % weeks
    if days > 0:
        output += " " + ungettext("%d day", "%d days", days) % days

    return output


def format_float(x):
    """
    Return a nice human readable version of a float.

    It will never return something that looks like zero for a non-zero number.

    """

    if x == 0:
        # It's zero, so return
        return "0"
    else:
        # How many decimal places should be show?
        # If x = 0.0002, then if we show to 2 decimal places it'll show 0.00,
        # which looks like zero.
        for exp in range(2, 6):
            if x > math.pow(10, -exp):
                return "{0:.{1}f}".format(x, exp)
            else:
                continue
        else:
            # Haven't found anything, so return a <tinynumber
            return "<{0:.{1}f}".format(math.pow(10, -exp), exp)

def calculate_rate(initial_date, initial_percent, current_date, current_percent, amount_left):
    days = (current_date - initial_date).days
    delta_percent = (current_percent - initial_percent)
    if delta_percent < 0.00001:
        # Tiny difference, so we presume that it's a float rounding error and
        # round this down to zero.
        # Without this, we get completion dates in the far future (like the
        # year 150,000) which isn't very useful, so we might as well presume
        # it'll never finish
        delta_percent = 0

    rate = delta_percent / days
    if rate == 0:
        days_left = None
        end_date = None
        human_readable_time_left = None
    else:
        days_left =  int(amount_left / rate)

        try:
            end_date = current_date + timedelta(days=days_left)
        except OverflowError:
            # timedelta gives OverflowError if the days is too far in the future,
            # so cap it, based on datetime.MAXYEAR (which is 9999)
            end_date = "the year {0:.0f}".format(datetime.today().year + (days_left/365))
        human_readable_time_left = days_to_string(days_left)


    return {
        'rate': format_float(rate), 'days_left':days_left, 'end_date':end_date,
        'initial_date': initial_date,
        'human_readable_time_left': human_readable_time_left,
    }


def many_range_rates(name):
    query_set = Progress.objects.filter(name=name+'-tds')
    most_recent_date, most_recent_percent = query_set.order_by("-when", "-id").values_list('when', 'percent')[0]
    amount_left = round(100 - most_recent_percent, 4)
    ## since start
    initial_date, initial_percent = query_set.order_by("when", "-id").values_list('when', 'percent')[0]
    ## since day before
    yesterday_percent = query_set.filter(when=(most_recent_date - timedelta(days=1))).order_by("-id").values_list('percent', flat=True)
    yesterday_percent = yesterday_percent[0] if len(yesterday_percent) > 0 else None

    # since last week
    week_percent = query_set.filter(when=(most_recent_date - timedelta(days=7))).order_by("-id").values_list('percent', flat=True)
    week_percent = week_percent[0] if len(week_percent) > 0 else None

    # since last month
    month_percent = query_set.filter(when=(most_recent_date - timedelta(days=30))).order_by("-id").values_list('percent', flat=True)
    month_percent = month_percent[0] if len(month_percent) > 0 else None

    # since 90 days ago
    day90_percent = query_set.filter(when=(most_recent_date - timedelta(days=90))).order_by("-id").values_list('percent', flat=True)
    day90_percent = day90_percent[0] if len(day90_percent) > 0 else None

    results = {
        'amount_left': amount_left,
    }
    if most_recent_date > initial_date:
        # If we're running on empty database, we won't have anything
        results['since_start'] = calculate_rate(initial_date, initial_percent, most_recent_date, most_recent_percent, amount_left)
    if yesterday_percent is not None:
        results['since_yesterday'] = calculate_rate((most_recent_date - timedelta(days=1)), yesterday_percent, most_recent_date, most_recent_percent, amount_left)
    if week_percent is not None:
        results['since_last_week'] = calculate_rate((most_recent_date - timedelta(days=7)), week_percent, most_recent_date, most_recent_percent, amount_left)
    if month_percent is not None:
        results['since_last_month'] = calculate_rate((most_recent_date - timedelta(days=30)), month_percent, most_recent_date, most_recent_percent, amount_left)
    if day90_percent is not None:
        results['since_90_days'] = calculate_rate((most_recent_date - timedelta(days=90)), day90_percent, most_recent_date, most_recent_percent, amount_left)


    return results


def rate(request):
    results = {}
    results['ireland'] = many_range_rates('ireland')
    results['counties'] = []
    for county in sorted(COUNTIES):
        results['counties'].append((county, many_range_rates(county)))



    return render_to_response('irish_townlands/rate.html', results,
        context_instance=RequestContext(request))


def _search_for(qs):

    counties = list(County.objects.filter(qs).order_by("name_tag").only("name_tag", "name_ga", "alt_name"))
    baronies = list(Barony.objects.filter(qs).select_related("county").order_by("name_tag").only("name_tag", "name_ga", "alt_name", 'county__name_tag'))
    civil_parishes = list(CivilParish.objects.filter(qs).order_by("name_tag").only("name_tag", "name_ga", "alt_name"))
    eds = list(ElectoralDivision.objects.filter(qs).select_related("county").order_by("name_tag").only("name_tag", "name_ga", "alt_name", 'county__name_tag'))
    townlands = list(Townland.objects.filter(qs).select_related("county", "barony", "civil_parish").order_by("name_tag"). only("name_tag", "name_ga", "alt_name", "county__name_tag", "barony__name_tag", "civil_parish__name_tag"))
    subtownlands = list(Subtownland.objects.filter(qs).select_related("county", "barony", "civil_parish", "townland").order_by("name_tag"). only("name_tag", "name_ga", "townland__name_tag"))

    return {
        'counties': counties, 'counties_num_results': len(counties),
        'baronies': baronies, 'baronies_num_results': len(baronies),
        'civil_parishes': civil_parishes, 'civil_parishes_num_results': len(civil_parishes),
        'eds': eds, 'eds_num_results': len(eds),
        'townlands': townlands, 'townlands_num_results': len(townlands),
        'subtownlands': subtownlands, 'subtownlands_num_results': len(subtownlands),
    }


def search(request):
    search_term = request.GET.get('q', '')

    search_term = search_term.strip()

    if '/' in search_term and ' ' not in search_term:
        # maybe an (old) URL. What they want is probably the last element
        terms = [x for x in search_term.split("/") if len(x.strip()) > 0]
        if len(terms) > 0:
            last = terms[-1]
            search_url = reverse('search') + "?" + urllib.urlencode({'q': last})
            return redirect(search_url)

    if search_term == '':
        return render_to_response('irish_townlands/search_results.html', {},
            context_instance=RequestContext(request))

    search_term = search_term.replace("-", " ")
    qs = Q(name_tag__icontains=search_term) | Q(name_ga__icontains=search_term) | Q(alt_name__icontains=search_term) | Q(alt_name_ga__icontains=search_term) | Q(name_census1901_tag__contains=search_term) | Q(name_census1911_tag__contains=search_term)

    search_results = _search_for(qs)

    # if there is only one, then redirect to it
    if search_results['counties_num_results'] + search_results['baronies_num_results'] + search_results['civil_parishes_num_results'] + search_results['eds_num_results'] + search_results['townlands_num_results'] + search_results['subtownlands_num_results'] == 1:
        obj = (search_results['counties'] + search_results['baronies'] + search_results['civil_parishes'] + search_results['eds'] + search_results['townlands'] + search_results['subtownlands'])[0]
        return redirect('view_area', url_path=obj.url_path)

    results = {
        'search_term': search_term,
        'counties': search_results['counties'],
        'counties_num_results': search_results['counties_num_results'],
        'baronies': search_results['baronies'],
        'baronies_num_results': search_results['baronies_num_results'],
        'civil_parishes': search_results['civil_parishes'],
        'civil_parishes_num_results': search_results['civil_parishes_num_results'],
        'eds': search_results['eds'],
        'eds_num_results': search_results['eds_num_results'],
        'townlands': search_results['townlands'],
        'townlands_num_results': search_results['townlands_num_results'],
        'subtownlands': search_results['subtownlands'],
        'subtownlands_num_results': search_results['subtownlands_num_results'],
    }

    return render_to_response('irish_townlands/search_results.html', results,
        context_instance=RequestContext(request))

def taginfo(request):
    domain = "http://www.townlands.ie"
    return HttpResponse(json.dumps(
        {
            "data_format": 1,
            "data_url": domain + reverse("taginfo"),
            "project": {
                "name": "Irish Townlands",
                "description": "Irish townlands, civil parishes and baronies",
                "doc_url": "https://github.com/rory/osm-irish-townlands",
                "project_url": domain,
                "icon_url": domain + static("logo_small.png"),
                "contact_name": "Rory McCann",
                "contact_email": "rory@technomancy.org"
            },
            "tags": [
                {
                    "key": "name"
                },
                {
                    "key": "name:ga",
                    "description": "Irish name"
                },
                {
                    "key": "alt_name",
                    "description": "Alternative name"
                },
                {
                    "key": "natural",
                    "value": "water",
                    "description": "Used to exclude water areas from completeness calculations"
                },
                {
                    "key": "water",
                    "description": "Used to exclude water areas from completeness calculations"
                },
                {
                    "key": "waterway",
                    "description": "Used to exclude water areas from completeness calculations"
                },
                {
                    "key": "boundary",
                    "value": "barony",
                    "description": "Barony"
                },
                {
                    "key": "boundary",
                    "value": "civil_parish",
                    "description": "Civil Parish"
                },
                {
                    "key": "boundary",
                    "value": "administrative"
                },
                {
                    "key": "admin_level",
                    "value": "6",
                    "description": "County"
                },
                {
                    "key": "admin_level",
                    "value": "9",
                    "description": "Electoral Division"
                },
                {
                    "key": "admin_level",
                    "value": "10",
                    "description": "Townland"
                },
                {
                    "key": "place",
                    "value": "locality",
                    "description": "Subtownlands"
                },
                {
                    "key": "locality",
                    "value": "subtownland",
                    "description": "Subtownlands"
                },
                {
                    "key": "attribution",
                    "description": "Shows the attribution of an object"
                },
                {
                    "key": "name:census1901",
                    "description": "The name of this area recorded in the 1901 census of Ireland & NI. Used for constructing links to census records"
                },
                {
                    "key": "name:census1911",
                    "description": "The name of this area recorded in the 1911 census of Ireland & NI. Used for constructing links to census records"
                },
                {
                    "key": "logainm:ref",
                    "description": "The id of this object in Logainm, the Placename Database of Ireland."
                },
                {
                    "key": "official_name:en",
                    "description": "The official English language name of this area. Taken from Logainm"
                },
                {
                    "key": "official_name:ga",
                    "description": "The official Irish language name of this area. Taken from Logainm"
                },
            ]
        }
    ))

def page(request, url_path):
    if url_path not in PAGES:
        return Http404
    else:
        last_update = get_last_update()
        tmpl_data = PAGES[url_path]
        tmpl_data['last_update'] = last_update
        return render_to_response('irish_townlands/page.html', tmpl_data,
            context_instance=RequestContext(request))
    

def mapper_details(request, osm_user):
    tmpl_data = {'osm_user': osm_user}
    tmpl_data['counties'] = County.objects.filter(osm_user=osm_user).order_by("name_tag")
    tmpl_data['baronies'] = Barony.objects.select_related('county').only("name_tag", 'name_ga', 'alt_name', 'url_path', 'county__name_tag').filter(osm_user=osm_user).order_by("name_tag")
    tmpl_data['civil_parishes'] = CivilParish.objects.select_related('county').only("name_tag", 'name_ga', 'alt_name', 'url_path', 'county__name_tag').filter(osm_user=osm_user).order_by("name_tag")
    tmpl_data['eds'] = ElectoralDivision.objects.select_related('county').only("name_tag", 'name_ga', 'alt_name', 'url_path', 'county__name_tag').filter(osm_user=osm_user).order_by("name_tag")
    tmpl_data['townlands'] = Townland.objects.select_related('county', 'barony', 'civil_parish').only("name_tag", 'name_ga', 'alt_name', 'url_path', 'county__name_tag', 'barony__name_tag', 'civil_parish__name_tag').filter(osm_user=osm_user).order_by("name_tag")

    return render_to_response('irish_townlands/mapper_details.html', tmpl_data,
            context_instance=RequestContext(request))

def stats_for_user(osm_user):
    results = {}
    total = 0
    for model, name in (
                (Townland, 'townland'), (CivilParish, 'civil_parish'),
                (Barony, 'barony'), (County, 'county'),
                (ElectoralDivision, 'ed') ):
        this_model =  model.objects.filter(osm_user=osm_user).count()
        total += this_model
        results[name] = this_model

    results['total'] = total
    return results

def get_all_mappers():
    mappers = set()
    for model, name in (
                (Townland, 'townland'), (CivilParish, 'civil_parish'),
                (Barony, 'barony'), (County, 'county'),
                (ElectoralDivision, 'ed') ):
        mappers.update(list(model.objects.exclude(osm_user=None).values_list('osm_user', flat=True).distinct()))

    return mappers


def mappers(request):
    all_mappers = sorted(list(get_all_mappers()))

    all_mappers = [(osm_user, stats_for_user(osm_user)) for osm_user in all_mappers]
    all_mappers.sort(key=lambda x: x[1]['total'], reverse=True)

    return render_to_response('irish_townlands/mappers.html', {'all_mappers': all_mappers},
            context_instance=RequestContext(request))

def group_by_username(model, start_date):
    next_date = start_date + timedelta(days=1)
    utc = datetime.utcnow().tzinfo
    this_datetime = datetime(start_date.year, start_date.month, start_date.day, 0, 0).replace(tzinfo=utc)
    next_datetime = datetime(next_date.year, next_date.month, next_date.day, 0, 0).replace(tzinfo=utc)

    results = defaultdict(list)
    for el in model.objects.filter(osm_timestamp__gte=this_datetime, osm_timestamp__lt=next_datetime).only("osm_user", "url_path", "name_tag").order_by("osm_user"):
        results[el.osm_user].append(el)

    return results

def detailed_stats_for_period(from_date, to_date):
    assert from_date <= to_date, (from_date, to_date)
    dates = []
    curr_date = from_date
    while curr_date <= to_date:
        dates.append(curr_date)
        curr_date += timedelta(days=1)

    result = []
    
    dates.sort(reverse=True)

    for date in dates:

        townlands = group_by_username(Townland, date)
        eds = group_by_username(ElectoralDivision, date)
        cps = group_by_username(CivilParish, date)
        baronies = group_by_username(Barony, date)
        counties = group_by_username(County, date)
        subtownlands = group_by_username(Subtownland, date)

        num_townlands = sum(len(l) for l in townlands.values())
        num_eds = sum(len(l) for l in eds.values())
        num_cps = sum(len(l) for l in cps.values())
        num_baronies = sum(len(l) for l in baronies.values())
        num_subtownlands = sum(len(l) for l in subtownlands.values())

        summary = []
        if num_townlands > 0:
            summary.append(ungettext("%d townland", "%d townlands", num_townlands) % num_townlands)
        if num_eds > 0:
            summary.append(ungettext("%d ED", "%d EDs", num_eds) % num_eds)
        if num_cps > 0:
            summary.append(ungettext("%d civil parish", "%d civil parishes", num_cps) % num_cps)
        if num_baronies > 0:
            summary.append(ungettext("%d barony", "%d baronies", num_baronies) % num_baronies)
        if num_subtownlands > 0:
            summary.append(ungettext("%d subtownland", "%d subtownlands", num_subtownlands) % num_subtownlands)
        if len(summary) == 0:
            summary.append(ugettext("No mapping activity"))

        summary = " ".join(summary)


        users = set(townlands.keys() + eds.keys() + cps.keys() + baronies.keys() + counties.keys() + subtownlands.keys())
        users = sorted(list(users))
        this_date_details = {
            'date': date,
            'summary': summary,
            'stats': [
                {'osm_user': osm_user,
                 'townlands': townlands.get(osm_user, []),
                 'eds': eds.get(osm_user, []),
                 'cps': cps.get(osm_user, []),
                 'baronies': baronies.get(osm_user, []),
                 'counties': counties.get(osm_user, []),
                 'subtownlands': subtownlands.get(osm_user, []),
                }
                for osm_user in users]}
        result.append(this_date_details)

    return result

def activity(request):
    if 'on' in request.GET:
        year, month, day = request.GET['on'].split("-")
        year, month, day = int(year), int(month), int(day)
        on_date = date(year, month, day)
        to_date = on_date
        from_date = on_date
    else:
        to_date = date.today() - timedelta(days=1)
        try:
            if 'to' in request.GET:
                year, month, day = request.GET['to'].split("-")
                year, month, day = int(year), int(month), int(day)
                to_date = date(year, month, day)
        except:
            pass

        from_date = to_date - timedelta(days=7)
        try:
            if 'from' in request.GET:
                year, month, day = request.GET['from'].split("-")
                year, month, day = int(year), int(month), int(day)
                from_date = date(year, month, day)
        except:
            pass


    stats = detailed_stats_for_period(from_date, to_date)

    return render_to_response('irish_townlands/activity.html', {'from': from_date, 'to': to_date, 'stats': stats},
            context_instance=RequestContext(request))


def activity_rss(request):
    to_date = date.today() - timedelta(days=1)
    from_date = to_date - timedelta(days=30)

    stats = detailed_stats_for_period(from_date, to_date)

    feed = feedgenerator.Rss201rev2Feed(
        title=u"Townlands.ie Activity",
        link=u"http://www.townlands.ie/progress/activity/",
        description=u"Irish Townlands mapping activity",
        language=u"en",
    )

    for period in stats:
        content = render_to_string("irish_townlands/activity_for_one_date.html", {'period': period}, context_instance=RequestContext(request))
        feed.add_item(
            title=u"Townlands.ie: " + period['summary'],
            link=u"http://www.townlands.ie/progress/activity/?on={}-{}-{}".format(period['date'].year, period['date'].month, period['date'].day),
            pubdate=period['date'],
            description=content)

    return HttpResponse(feed.writeString('UTF-8'), mimetype='application/rss+xml')

def townland_index_alphabetical(request):
    return townland_index(request, should_group=False)

def townland_index_grouped(request):
    return townland_index(request, should_group=True)

def townland_index(request, should_group=False):
    incl_irish = request.GET.get("incl_irish", "yes") == "yes"

    townlands = Townland.objects.select_related("barony", "civil_parish", "county").only("url_path", "name_tag", "name_ga", "alt_name", "alt_name_ga", "place", "area_m2", "barony__name_tag", "county__name_tag", "civil_parish__name_tag")

    results = []

    num_townlands = 0
    for t in townlands:
        alternatives = t.expand_to_alternatives(incl_irish=incl_irish, desc=('medium' if should_group else 'long'))
        if should_group:
            # Big hack here to get the sorting I want. Added zero width space
            # (\ufeff) before each 'unknown' element so that it would be sorted
            # last (e.g. "barony unknown" section will be the last entry for
            # that county under all the actual baronies we know about.
            alternatives = [
                (format_html(u"<span class=\"text-muted\">Co.</span> {}", t.county.name) if t.county else mark_safe(u"\ufeff<i class=\"text-muted\">(County unknown)</i>"),
                 format_html(u"<span class=\"text-muted\">Barony of</span> {}", t.barony.name) if t.barony else mark_safe(u'\ufeff<i class=\"text-muted\">(Barony unknown)</i>'),
                 format_html(u"{} <span class=\"text-muted\">Civil Parish</span>", t.civil_parish.name) if t.civil_parish else mark_safe(u'\ufeff<i class=\"text-muted\">(Civil Parish unknown)</i>'),
                 townland_key, text) for (townland_key, text) in alternatives]
        results.extend(alternatives)
        num_townlands += 1

    results.sort()

    view_name = 'townland_index_grouped' if should_group else 'townland_index_alphabetical'

    return render_to_response('irish_townlands/list.html', {'townlands': results, 'num_townlands': num_townlands, 'today': date.today(), 'should_group': should_group, 'incl_irish': incl_irish, 'view_name': view_name},
            context_instance=RequestContext(request))

def mappinghistory(request, should_group=False):
    townlands = Townland.objects.select_related("barony", "civil_parish", "county").only("url_path", "name_tag", "name_ga", "alt_name", "alt_name_ga", "place", "area_m2", "barony__name_tag", "county__name_tag", "civil_parish__name_tag", "osm_timestamp", "osm_user").order_by("osm_timestamp", "name_tag")

    return render_to_response('irish_townlands/mappinghistory.html', {'townlands': townlands},
            context_instance=RequestContext(request))


def lookup_by_logainm(request, logainm_ref):
    qs = Q(logainm_ref=logainm_ref)

    search_results = _search_for(qs)

    # if there is only one, then redirect to it
    if search_results['counties_num_results'] + search_results['baronies_num_results'] + search_results['civil_parishes_num_results'] + search_results['eds_num_results'] + search_results['townlands_num_results'] + search_results['subtownlands_num_results'] == 1:
        obj = (search_results['counties'] + search_results['baronies'] + search_results['civil_parishes'] + search_results['eds'] + search_results['townlands'] + search_results['subtownlands'])[0]
        return redirect('view_area', url_path=obj.url_path)

    results = {
        'search_term': logainm_ref,
        'counties': search_results['counties'],
        'counties_num_results': search_results['counties_num_results'],
        'baronies': search_results['baronies'],
        'baronies_num_results': search_results['baronies_num_results'],
        'civil_parishes': search_results['civil_parishes'],
        'civil_parishes_num_results': search_results['civil_parishes_num_results'],
        'eds': search_results['eds'],
        'eds_num_results': search_results['eds_num_results'],
        'townlands': search_results['townlands'],
        'townlands_num_results': search_results['townlands_num_results'],
        'subtownlands': search_results['subtownlands'],
        'subtownlands_num_results': search_results['subtownlands_num_results'],
    }

    return render_to_response('irish_townlands/search_results.html', results,
        context_instance=RequestContext(request))

