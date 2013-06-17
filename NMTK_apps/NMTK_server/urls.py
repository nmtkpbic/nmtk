from django.conf.urls import patterns, include, url

from NMTK_server import api
from tastypie.api import Api
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

v1_api = Api(api_name='v1')
v1_api.register(api.DataFileResource())
v1_api.register(api.UserResource())
v1_api.register(api.ToolResource())
v1_api.register(api.ToolConfigResource())
v1_api.register(api.JobResource())
v1_api.register(api.JobStatusResource())
    

urlpatterns = patterns('',
   url('^$', 'NMTK_server.views.submitJob', {}, name='submitJob'),
   url('^tools/result$', 'NMTK_server.views.processResults', {}, name='processSuccessResults'),
   url('^tools/update$', 'NMTK_server.views.updateStatus', {}, name='updateStatus'),
   url('^submit-job-to-tool$', 'NMTK_server.views.configureJob', {}, name='configureJob'),
   url('^refresh-status/(?P<job_id>[^/]*)$', 'NMTK_server.views.refreshStatus', {}, name='refreshStatus'),
   url('^results/(?P<job_id>[^/]*)$', 'NMTK_server.views.viewResults', {}, name='viewResults'),   
   url('^downloadResults/(?P<job_id>[^/]*)$', 'NMTK_server.views.downloadResults', {}, name='downloadResults'),   
   url('^downloadDataFile/(?P<file_id>[^/]*)$', 'NMTK_server.views.downloadDataFile', {}, name='NMTK_server.download_datafile'),
   url('^downloadGeoJsonFile/(?P<file_id>[^/]*)$', 'NMTK_server.views.downloadGeoJsonFile', {}, name='NMTK_server.download_geojson_datafile'),
   url(r'^login/$', 'django.contrib.auth.views.login', name='login_page'),
   url(r'^logout/$', 'NMTK_server.views.logout_page', name='logout'),
   # Uncomment the admin/doc line below to enable admin documentation:
   # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
   # Uncomment the next line to enable the admin:
   url(r'^admin/', include(admin.site.urls)),
   url(r'^api/', include(v1_api.urls)),
)
