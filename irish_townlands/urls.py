from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('irish_townlands.views',
    url(r'progress/$', 'progress', name='progress' ),
    url(r'^$', 'view_area', name='view_area' ),
    url(r'(?P<url_path>[-\w\d/]+)/$', 'view_area', name='view_area' ),
)
