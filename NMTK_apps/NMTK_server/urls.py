from django.conf.urls import patterns, include, url
from NMTK_server import signals

urlpatterns = patterns('',
   url('^$', 'NMTK_server.views.submitJob', {}, name='submitJob'),
   url('^tools/result$', 'NMTK_server.views.processResults', {}, name='processSuccessResults'),
   url('^tools/update$', 'NMTK_server.views.updateStatus', {}, name='updateStatus'),
   url('^submit-job-to-tool$', 'NMTK_server.views.configureJob', {}, name='configureJob'),
   url('^refresh-status/(?P<job_id>[^/]*)$', 'NMTK_server.views.refreshStatus', {}, name='refreshStatus'),
   url('^results/(?P<job_id>[^/]*)$', 'NMTK_server.views.viewResults', {}, name='viewResults'),   
   url('^downloadResults/(?P<job_id>[^/]*)$', 'NMTK_server.views.downloadResults', {}, name='downloadResults'),
)
