from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'NMTK_apps.views.home', name='home'),
    # url(r'^NMTK_apps/', include('NMTK_apps.foo.urls')),
    # This one is used to generate the tool index for this tool server.
    url(r'^index/?$', 'NMTK_tools.views.toolIndex', {}, name='tool_index'),
    url(r'^MN_model/', include('MN_model.urls')),
    url(r'^SF_model/', include('SF_model.urls')),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)

# By default, the server is enabled.  However, if this host should only
# support tools (and no NMTK server) then this should be set to False
if getattr(settings, 'NMTK_ENABLE_SERVER', True):
    urlpatterns += patterns('',
        url(r'^server/', include('NMTK_server.urls')),
    )


from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# ... the rest of your URLconf here ...

urlpatterns += staticfiles_urlpatterns()