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
# Create your views here.
from django.conf import settings
from django.http import HttpResponse
from NMTK_apps import urls
import json
import logging
logger=logging.getLogger(__name__)

def toolIndex(request):
    '''
    Auto discover all the tools, assuming they use a simple
    urlpattern for the tool base path, and return a list of those
    tools.  
    
    The assumption here is that each tool will use a module called
    tool_configs, which contains an attribute called 'tools', which
    contains a list of the tools supported, which should match
    the urlpatterns defined in the tool.
    '''
    tool_apps={}
    for app in settings.INSTALLED_APPS:
        module="%s.tool_configs" % (app,)
        try:
            config=__import__(module)
            tool_apps[app]=[config.tool_configs]
            logger.debug('Located tool config for %s (%s)', app, config)
        except:
            logger.debug('App %s has no tool config', module)
    for pattern in urls.urlpatterns:
        if not hasattr(pattern,'urlconf_name') or not \
               hasattr(pattern.urlconf_name, '__name__'):
            continue
        app_name=getattr(pattern, 'urlconf_name').__name__.rsplit('.urls',1)[0]
        logger.debug('App Name is %s', app_name)
        if tool_apps.has_key(app_name):
            tool_apps[app_name].append(getattr(pattern,'_regex').strip('^$'))
            logger.debug('Found path for %s as %s', app_name, 
                         tool_apps[app_name])
    result=[]
    for app, data in tool_apps.iteritems():
        tool_config=data[0]
        for tool in data[0].tools:
            if isinstance(data[-1],str):
                url="%s%s" % (data[-1], tool,)
                result.append(url)
    logger.debug("Tool list is %s" , result)
    return HttpResponse(json.dumps(result), 
                        content_type='application/json')
            