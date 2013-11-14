from django.http import Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
import re

from .models import Metadata, Townland, CivilParish, Barony, County, Error

def progress(request):
    try:
        last_update = Metadata.objects.get(key="lastupdate").value
    except Metadata.DoesNotExist:
        last_update = "N/A"
    counties = County.objects.order_by('name').all()
    errors = Error.objects.all().values_list('message', flat=True)
    return render_to_response('irish_townlands/progress.html', {'counties':counties, 'last_update':last_update, 'errors':errors}, context_instance=RequestContext(request))

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
            'counties': County.objects.prefetch_related("townlands", "baronies", "civil_parishes").order_by('name').all(),
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
