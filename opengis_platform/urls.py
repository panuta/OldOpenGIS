import os

from django.conf.urls.defaults import *
from django.conf import settings

from django.views.static import serve

from django.contrib.gis import admin
admin.autodiscover()

urlpatterns = patterns('',
	(r'^', include('opengis_platform.opengis.urls')),
	
	(r'^admin/(.*)', admin.site.root),
	(r'^accounts/', include('registration.backends.default.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns('', 
        (r'^m/(?P<path>.*)$', serve, {
            'document_root' : os.path.join(os.path.dirname(__file__), "media")
        })
    )