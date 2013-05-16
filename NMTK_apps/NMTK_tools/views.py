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
        if not hasattr(pattern,'urlconf_name'):
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
            