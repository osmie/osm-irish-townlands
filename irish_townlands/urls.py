from django.conf.urls import *
from django.conf import settings

urlpatterns = patterns('irish_townlands.views',
    url(r'progress/$', 'progress', name='progress' ),
    url(r'progress/duplicatenames/$', 'duplicatenames', name='duplicatenames' ),
    url(r'progress/rate/$', 'rate', name='rate' ),
    url(r'(?P<url_path>[-\w\d/]+)/debug/$', 'county_debug', name='county_debug' ),
    url(r'^$', 'view_area', name='view_area' ),
    url(r'(?P<url_path>[-\w\d/]+)/$', 'view_area', name='view_area' ),
)
