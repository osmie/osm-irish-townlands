"""Views."""
from __future__ import division
import re
from datetime import timedelta, datetime
import math
import json

from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.db.models import Sum, Count, Q
from django.contrib.staticfiles.templatetags.staticfiles import static


from .models import Metadata, Townland, CivilParish, Barony, County, ElectoralDivision, Error, Progress
from .pages import PAGES

COUNTIES = [u'Antrim', u'Armagh', u'Carlow', u'Cavan', u'Clare', u'Cork',
            u'Derry', u'Donegal', u'Down', u'Dublin', u'Fermanagh', u'Galway',
            u'Kerry', u'Kildare', u'Kilkenny', u'Laois', u'Leitrim',
            u'Limerick', u'Longford', u'Louth', u'Mayo', u'Meath', u'Monaghan',
            u'Offaly', u'Roscommon', u'Sligo', u'Tipperary', u'Tyrone',
            u'Waterford', u'Westmeath', u'Wexford', u'Wicklow']



def progress(request):
    try:
        last_update = Metadata.objects.get(key="lastupdate").value
    except Metadata.DoesNotExist:
        last_update = "N/A"
    counties = County.objects.order_by('name').all()
    errors = Error.objects.all().values_list('message', flat=True)

    area_of_ireland_incl_water = County.objects.all().aggregate(Sum('area_m2'))['area_m2__sum'] or 0
    water_of_ireland = County.objects.all().aggregate(Sum('water_area_m2'))['water_area_m2__sum'] or 0
    area_of_ireland_excl_water = area_of_ireland_incl_water - water_of_ireland
    area_of_ireland = area_of_ireland_excl_water

    area_of_all_townlands = Townland.objects.all().aggregate(Sum('area_m2'))['area_m2__sum'] or 0
    area_of_all_civil_parishes = CivilParish.objects.all().aggregate(Sum('area_m2'))['area_m2__sum'] or 0
    area_of_all_baronies = Barony.objects.all().aggregate(Sum('area_m2'))['area_m2__sum'] or 0

    if area_of_ireland == 0:
        townland_progress = civil_parish_progress = barony_progress = 0
    else:
        townland_progress = ( area_of_all_townlands / area_of_ireland ) * 100
        civil_parish_progress = ( area_of_all_civil_parishes / area_of_ireland ) * 100
        barony_progress = ( area_of_all_baronies / area_of_ireland ) * 100

    return render_to_response('irish_townlands/progress.html',
        {
            'counties':counties, 'last_update':last_update, 'errors':errors,
            'townland_progress': townland_progress, 'civil_parish_progress': civil_parish_progress,
            'barony_progress': barony_progress,
         },
        context_instance=RequestContext(request))


def duplicatenames(request):
    # Dupe names. Nothing wrong with duplicate names, it happens
    duplicate_townland_names = []
    duplicate_names = Townland.objects.all().values("name").annotate(count=Count('name')).filter(count__gte=2).order_by('-count', 'name')
    for item in duplicate_names:
        townland_name, townland_count = item['name'], item['count']
        townlands = Townland.objects.filter(name=townland_name).order_by("county__name", "barony__name", "civil_parish__name").values('url_path', 'county__name', 'barony__name', 'civil_parish__name')
        duplicate_townland_names.append({'name': townland_name, 'count': townland_count, 'townlands': townlands})

    return render_to_response('irish_townlands/duplicatenames.html',
        {
            'duplicate_townland_names': duplicate_townland_names,
         },
        context_instance=RequestContext(request))

def county_debug(request, url_path):
    try:
        last_update = Metadata.objects.get(key="lastupdate").value
    except Metadata.DoesNotExist:
        last_update = "N/A"

    # County debug page
    try:
        # strip debug from url to get county
        url_path = re.sub('debug/$', '', url_path)
        x = County.objects.select_related().get(url_path=url_path)
        return render_to_response('irish_townlands/countydebug_detail.html', {'county': x, 'last_update': last_update}, context_instance=RequestContext(request))
    except:
        # Couldn't find county
        raise Http404("County not found")

def view_area(request, url_path=None):
    try:
        last_update = Metadata.objects.get(key="lastupdate").value
    except Metadata.DoesNotExist:
        last_update = "N/A"

    # County index page
    if url_path in ['all', None]:
        return render_to_response('irish_townlands/index.html', {
            'counties': County.objects.only('name', 'url_path').order_by('name').all(),
            'num_baronies': Barony.objects.all().count(),
            'num_civil_parishes': CivilParish.objects.all().count(),
            'num_eds': ElectoralDivision.objects.all().count(),
            'num_townlands': Townland.objects.all().count(),
            'last_update': last_update,
            }, context_instance=RequestContext(request))

    # Detail pages
    for model, name in (
                (Townland, 'townland'), (CivilParish, 'civil_parish'),
                (Barony, 'barony'), (County, 'county'),
                (ElectoralDivision, 'ed') ):
        try:
            x = model.objects.select_related().get(url_path=url_path)
            return render_to_response('irish_townlands/'+name+'_detail.html', {name: x, name+"_name": x.name, 'last_update': last_update}, context_instance=RequestContext(request))
        except model.DoesNotExist:
            continue  #  on to next model

    # nothing by here?
    raise Http404()

def days_to_string(days):
    days = int(days)
    years, days = divmod(days, 365)
    months, days = divmod(days, 30)
    weeks, days = divmod(days, 7)
    output = ""
    if years > 0:
        output += "%d years" % years
    if months > 0:
        output += " %d months" % months
    if weeks > 0:
        output += " %d weeks" % weeks
    if days > 0:
        output += " %d days" % days

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

def search(request):
    search_term = request.GET.get('q', '').strip()

    qs = Q(name__icontains=search_term) | Q(name_ga__icontains=search_term) | Q(alt_name__icontains=search_term)

    counties = list(County.objects.filter(qs).order_by("name").only("name", "name_ga", "alt_name"))
    counties_num_results = len(counties)
    baronies = list(Barony.objects.filter(qs).select_related("county").order_by("name").only("name", "name_ga", "alt_name", 'county__name'))
    baronies_num_results = len(baronies)
    civil_parishes = list(CivilParish.objects.filter(qs).select_related("county").order_by("name").only("name", "name_ga", "alt_name", 'county__name'))
    civil_parishes_num_results = len(civil_parishes)
    eds = list(ElectoralDivision.objects.filter(qs).select_related("county").order_by("name").only("name", "name_ga", "alt_name", 'county__name'))
    eds_num_results = len(civil_parishes)
    townlands = list(Townland.objects.filter(qs).select_related("county", "barony", "civil_parish").order_by("name"). only("name", "name_ga", "alt_name", "county__name", "barony__name", "civil_parish__name"))
    townlands_num_results = len(townlands)

    results = {
        'counties': counties,
        'counties_num_results': counties_num_results,
        'baronies': baronies,
        'baronies_num_results': baronies_num_results,
        'civil_parishes': civil_parishes,
        'civil_parishes_num_results': civil_parishes_num_results,
        'eds': eds,
        'eds_num_results': eds_num_results,
        'townlands': townlands,
        'townlands_num_results': townlands_num_results,
        'search_term': search_term,
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
                }
            ]
        }
    ))

def page(request, url_path):
    if url_path not in PAGES:
        return Http404
    else:
        return render_to_response('irish_townlands/page.html', PAGES[url_path])
    

def mapper_details(request, osm_user):
    tmpl_data = {'osm_user': osm_user}
    tmpl_data['counties'] = County.objects.filter(osm_user=osm_user).order_by('name')
    tmpl_data['baronies'] = Barony.objects.select_related('county').only("name", 'name_ga', 'alt_name', 'url_path', 'county__name').filter(osm_user=osm_user).order_by('name')
    tmpl_data['civil_parishes'] = CivilParish.objects.select_related('county').only("name", 'name_ga', 'alt_name', 'url_path', 'county__name').filter(osm_user=osm_user).order_by('name')
    tmpl_data['eds'] = ElectoralDivision.objects.select_related('county').only("name", 'name_ga', 'alt_name', 'url_path', 'county__name').filter(osm_user=osm_user).order_by('name')
    tmpl_data['townlands'] = Townland.objects.select_related('county', 'barony', 'civil_parish').only("name", 'name_ga', 'alt_name', 'url_path', 'county__name', 'barony__name', 'civil_parish__name').filter(osm_user=osm_user).order_by('name')

    return render_to_response('irish_townlands/mapper_details.html', tmpl_data)
