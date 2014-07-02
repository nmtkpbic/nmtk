#!/usr/bin/env python
# Non-Motorized Toolkit
# Copyright (c) 2014 Open Technology Group Inc. (A North Carolina Corporation)
# Developed under Federal Highway Administration (FHWA) Contracts:
# DTFH61-12-P-00147 and DTFH61-14-P-00108
# 
# Redistribution and use in source and binary forms, with or without modification, 
# are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright notice, 
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright 
#       notice, this list of conditions and the following disclaimer 
#       in the documentation and/or other materials provided with the distribution.
#     * Neither the name of the Open Technology Group, the name of the 
#       Federal Highway Administration (FHWA), nor the names of any 
#       other contributors may be used to endorse or promote products 
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT 
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS 
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL 
# Open Technology Group Inc BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT 
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF 
# USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED 
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT 
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
from django.conf.urls import patterns, include, url
from django.conf import settings
from django.views.generic import RedirectView




urlpatterns = patterns('',
    # This one is used to generate the tool index for this tool server.
    url(r'^index/$', 'NMTK_tools.views.toolIndex', {}, name='tool_index'),
    url(r'^MN_model/', include('MN_model.urls')),
    url(r'^SF_model/', include('SF_model.urls')),
)
if not settings.PRODUCTION:
   urlpatterns += patterns('',
                           url(r'^test_tool/', include('test_tool.urls')),
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
# Enable the UI if the app is in the list of installed applications.
if 'NMTK_ui' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        url(r'^ui/', include('NMTK_ui.urls')),
    )
    
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# ... the rest of your URLconf here ...

urlpatterns += staticfiles_urlpatterns()