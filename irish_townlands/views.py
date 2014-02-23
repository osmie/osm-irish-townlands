"""Views."""

from django.http import Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Sum, Count
import re

from .models import Metadata, Townland, CivilParish, Barony, County, Error


def progress(request):
    try:
        last_update = Metadata.objects.get(key="lastupdate").value
    except Metadata.DoesNotExist:
        last_update = "N/A"
    counties = County.objects.order_by('name').all()
    errors = Error.objects.all().values_list('message', flat=True)

    area_of_ireland = County.objects.all().aggregate(Sum('area_m2'))['area_m2__sum'] or 0
    area_of_all_townlands = Townland.objects.all().aggregate(Sum('area_m2'))['area_m2__sum'] or 0
    area_of_all_civil_parishes = CivilParish.objects.all().aggregate(Sum('area_m2'))['area_m2__sum'] or 0
    area_of_all_baronies = Barony.objects.all().aggregate(Sum('area_m2'))['area_m2__sum'] or 0

    if area_of_ireland == 0:
        townland_progress = civil_parish_progress = barony_progress = 0
    else:
        townland_progress = ( area_of_all_townlands / area_of_ireland ) * 100
        civil_parish_progress = ( area_of_all_civil_parishes / area_of_ireland ) * 100
        barony_progress = ( area_of_all_baronies / area_of_ireland ) * 100

    # Dupe names. Nothing wrong with duplicate names, it happens
    duplicate_townland_names = []
    duplicate_names = Townland.objects.all().values("name").annotate(count=Count('name')).filter(count__gte=2).order_by('-count', 'name')
    for item in duplicate_names:
        townland_name, townland_count = item['name'], item['count']
        townlands = Townland.objects.filter(name=townland_name).order_by("county__name", "barony__name", "civil_parish__name").values('url_path', 'county__name', 'barony__name', 'civil_parish__name')
        duplicate_townland_names.append({'name': townland_name, 'count': townland_count, 'townlands': townlands})

    return render_to_response('irish_townlands/progress.html',
        {
            'counties':counties, 'last_update':last_update, 'errors':errors,
            'townland_progress': townland_progress, 'civil_parish_progress': civil_parish_progress,
            'barony_progress': barony_progress,
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
            'last_update': last_update,
            }, context_instance=RequestContext(request))

    # Detail pages
    for model, name in ( (Townland, 'townland'), (CivilParish, 'civil_parish'), (Barony, 'barony'), (County, 'county')):
        try:
            x = model.objects.select_related().get(url_path=url_path)
            return render_to_response('irish_townlands/'+name+'_detail.html', {name: x, 'last_update': last_update}, context_instance=RequestContext(request))
        except model.DoesNotExist:
            continue  #  on to next model

    # nothing by here?
    raise Http404()
