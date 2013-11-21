from django.conf.urls import patterns, include, url
urlpatterns = patterns('',
   url('^$', 'NMTK_ui.views.nmtk_ui', {}, name='nmtk_ui_nmtk_ui'),
   )