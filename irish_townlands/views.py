from django.http import Http404
from django.shortcuts import render_to_response
from django.template import RequestContext

from .models import Metadata, Townland, CivilParish, Barony, County, Error

def progress(request):
    try:
        last_update = Metadata.objects.get(key="lastupdate").value
    except Metadata.DoesNotExist:
        last_update = "N/A"
    counties = County.objects.order_by('name').all()
    errors = Error.objects.all().values_list('message', flat=True)
    return render_to_response('longtaillists/progress.html', {'counties':counties, 'last_update':last_update, 'errors':errors}, context_instance=RequestContext(request))


def view_area(request, url_path=None):
    try:
        last_update = Metadata.objects.get(key="lastupdate").value
    except Metadata.DoesNotExist:
        last_update = "N/A"
    if url_path in ['all', None ]:
        return render_to_response('irish_townlands/index.html', {
            'townlands': Townland.objects.select_related("county").order_by("name").all(),
            'counties': County.objects.prefetch_related("townlands", "baronies", "civil_parishes").order_by('name').all(),
            'baronies': Barony.objects.prefetch_related("townlands").select_related("county").order_by("county__name", "name").all(),
            'civil_parishes': CivilParish.objects.prefetch_related("townlands").select_related("county").order_by("county__name", "name").all(),
            'last_update': last_update,
            }, context_instance=RequestContext(request))

    for model, name in ( (Townland, 'townland'), (CivilParish, 'civil_parish'), (Barony, 'barony'), (County, 'county')):
        try:
            x = model.objects.select_related().get(url_path=url_path)
            return render_to_response('irish_townlands/'+name+'_detail.html', {name: x, 'last_update': last_update}, context_instance=RequestContext(request))
        except model.DoesNotExist:
            continue  #  on to next model

    # nothing by here?
    raise Http404()
