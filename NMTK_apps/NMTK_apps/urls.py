from django.conf.urls import patterns, include, url
from django.conf import settings
from django.views.generic import RedirectView




urlpatterns = patterns('',
    # This one is used to generate the tool index for this tool server.
    url(r'^index/$', 'NMTK_tools.views.toolIndex', {}, name='tool_index'),
    url(r'^MN_model/', include('MN_model.urls')),
    url(r'^SF_model/', include('SF_model.urls')),
)

# If the NMTK_server app is installed, then we need to include this
# other stuff - the views, etc. for the server.
#
# The same is true for the django admin interface - it is only available
# on the NMTK server, not any tool server(s)
#if getattr(settings, 'NMTK_ENABLE_SERVER', True):
if 'NMTK_server' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        url(r'^$', RedirectView.as_view(url='/server/')),
        url(r'^server/', include('NMTK_server.urls')),
    )
else:
    urlpatterns += patterns('',
        url(r'^$', RedirectView.as_view(url='/index/')),
    )

from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# ... the rest of your URLconf here ...

urlpatterns += staticfiles_urlpatterns()