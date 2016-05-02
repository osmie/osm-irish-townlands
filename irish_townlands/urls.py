from django.conf.urls import url
from django.views.generic import RedirectView

from django.conf import settings

from .views import *

urlpatterns = [

    url(r'^index/$', townland_index_alphabetical, name='townland_index_alphabetical' ),
    url(r'^index/grouped/$', townland_index_grouped, name='townland_index_grouped' ),

    url(r'^taginfo.json$', taginfo, name='taginfo'),
    url(r'^progress/$', progress, name='progress' ),
    url(r'^search/$', search, name='search' ),
    url(r'^mappers/$', mappers, name='mappers' ),
    url(r'^mapper/(?P<osm_user>.+)/$', mapper_details, name='mapper_details' ),
    url(r'^pages?/(?P<url_path>[-\w\d/]+)/$', page, name='page' ),

    url(r'^progress/duplicatenames/$', duplicatenames, name='duplicatenames' ),
    url(r'^progress/rate/$', rate, name='rate' ),
    url(r'^progress/logainmqa/$', logainmqa, name='logainmqa' ),

    url(r'^progress/activity/$', activity, name='activity' ),
    url(r'^progress/activity/rss/$', activity_rss, name='activity_rss' ),
    url(r'^activity/$', RedirectView.as_view(pattern_name='activity', permanent=True)),
    url(r'^progress/mappinghistory/$', mappinghistory, name='mappinghistory' ),
    url(r'^by/logainm/(?P<logainm_ref>[0-9]+)/$', lookup_by_logainm, name='lookup_by_logainm' ),
    url(r'^by/osm_id/(?P<osm_id>-?[0-9]+)/$', lookup_by_osm_id, name='lookup_by_osm_id' ),

    url(r'^(?P<url_path>[-\w\d/]+)/debug/$', county_debug, name='county_debug' ),
    url(r'^$', view_area, name='view_area' ),

    # This must go at the end
    url(r'^(?P<url_path>[-\w\d/]+)/$', view_area, name='view_area' ),

]
