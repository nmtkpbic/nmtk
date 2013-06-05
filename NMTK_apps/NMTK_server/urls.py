from django.conf.urls import patterns, include, url

from NMTK_server import signals
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
   url('^$', 'NMTK_server.views.submitJob', {}, name='submitJob'),
   url('^tools/result$', 'NMTK_server.views.processResults', {}, name='processSuccessResults'),
   url('^tools/update$', 'NMTK_server.views.updateStatus', {}, name='updateStatus'),
   url('^submit-job-to-tool$', 'NMTK_server.views.configureJob', {}, name='configureJob'),
   url('^refresh-status/(?P<job_id>[^/]*)$', 'NMTK_server.views.refreshStatus', {}, name='refreshStatus'),
   url('^results/(?P<job_id>[^/]*)$', 'NMTK_server.views.viewResults', {}, name='viewResults'),   
   url('^downloadResults/(?P<job_id>[^/]*)$', 'NMTK_server.views.downloadResults', {}, name='downloadResults'),
   url(r'^login/$', 'django.contrib.auth.views.login', name='login_page'),
   # Uncomment the admin/doc line below to enable admin documentation:
   # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
   # Uncomment the next line to enable the admin:
   url(r'^admin/', include(admin.site.urls)),
)
