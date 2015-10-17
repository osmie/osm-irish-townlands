from django.conf.urls import *
from django.views.generic import RedirectView

from django.conf import settings

urlpatterns = patterns('irish_townlands.views',

    url(r'^index/$', 'townland_index_alphabetical', name='townland_index_alphabetical' ),
    url(r'^index/grouped/$', 'townland_index_grouped', name='townland_index_grouped' ),

    url(r'^taginfo.json$', 'taginfo', name='taginfo'),
    url(r'^progress/$', 'progress', name='progress' ),
    url(r'^search/$', 'search', name='search' ),
    url(r'^mappers/$', 'mappers', name='mappers' ),
    url(r'^mapper/(?P<osm_user>.+)/$', 'mapper_details', name='mapper_details' ),
    url(r'^page/(?P<url_path>[-\w\d/]+)/$', 'page', name='page' ),

    url(r'^progress/duplicatenames/$', 'duplicatenames', name='duplicatenames' ),
    url(r'^progress/rate/$', 'rate', name='rate' ),

    url(r'^progress/activity/$', 'activity', name='activity' ),
    url(r'^progress/activity/rss/$', 'activity_rss', name='activity_rss' ),
    url(r'^activity/$', RedirectView.as_view(pattern_name='activity')),
    url(r'^progress/mappinghistory/$', 'mappinghistory', name='mappinghistory' ),

    url(r'^(?P<url_path>[-\w\d/]+)/debug/$', 'county_debug', name='county_debug' ),
    url(r'^$', 'view_area', name='view_area' ),
    url(r'^(?P<url_path>[-\w\d/]+)/$', 'view_area', name='view_area' ),

    url(r'^by/logainm/(?P<logainm_ref>[\d]+)/$', 'lookup_by_logainm', name='lookup_by_logainm' ),
)
