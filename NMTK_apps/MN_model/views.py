# Create your views here.
import json
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import SuspiciousOperation, PermissionDenied
from django.forms.models import model_to_dict
from django.conf import settings
from NMTK_apps.helpers import server_api
from NMTK_apps import decorators
import os
import tempfile
from MN_model import tasks
import logging
logger=logging.getLogger(__name__)
import hmac
import hashlib
import tool_configs
import os, stat

def toolBase(request, tool_name):
    '''
    This is the "base url" for the tool.  Generally, it doesn't do anything
    but there are several spots where we need to output it (for example, in 
    config) so this particular view is just here for the reverse-urlpattern.
    '''
    return HttpResponse('%s' % (tool_name,))

@csrf_exempt
def generateToolConfiguration(request, tool_name):
    '''
    Simply take the configuration for a tool from the tool_configs table,
    substitute in any specific URL parameters, then return the config
    as a json object to the requestor.
    '''
    if not hasattr(tool_configs, tool_name):
        raise Http404
    config=getattr(tool_configs, tool_name)
    # Add in the host and route data...
    config['host']={'url': request.build_absolute_uri('/'),
                    'route': reverse('tool_base',  
                                     kwargs={'tool_name': tool_name}) }
    for k in config['documentation']['links']:
        config['documentation']['links'][k]=request.build_absolute_uri('/') + \
                                            reverse('MN_Documentation',
                                                    kwargs={'tool_name': tool_name})
    return HttpResponse(json.dumps(config),
                        content_type='application/json')

@csrf_exempt
def generateDocs(request, tool_name):
    '''
    We put the HTML for documentation in the docs/ directory, this just serves 
    up those files to the user.
    '''
    return render(request, 'MN_model/docs/%s.html' % (tool_name.lower(),),)

@csrf_exempt
@decorators.nmtk # Valid request required to run the model.
def runModel(request, tool_name):
    '''
    This view will receive a request to run a tool and perform all the 
    relevant security/content checks.  It then calls the tool processing
    function via a celery task.  This allows us to immediately return
    a response to the client, and then the processing task can update the
    status to the NMTK server.
    '''
    logger.debug('Received request for processing!')
    # Read the tool configuration - this lets us just put the config in one place.
    if 'ols' in tool_name.lower():
        perform_exp=False
    if 'binomial' in tool_name.lower():
        perform_exp=True
    config=json.loads(generateToolConfiguration(request, tool_name).content)
    # Grab the uploaded files and store them on the file system, preserve
    # the extension, since OGR might need it to determine the driver
    # to use to read the file. 
    
    # So we expect there to be two keys for the uploaded files here,
    # config - for the config object
    # data - for the data object.
    logger.debug('config in request.FILES: %s', 'config' in request.FILES)
    logger.debug('data in request.FILES: %s', 'data' in request.FILES)
    if not ('config' in request.FILES and 'data' in request.FILES):
        raise SuspiciousOperation('A file and configuration must provided ' +
                                  ' in the payload.')
    filename=request.FILES['data'].name
    extension=os.path.splitext(filename)[1]
    outfile=tempfile.NamedTemporaryFile(suffix=extension, 
                                        prefix='nmtk_upload_',
                                        delete=False)
    outfile.write(request.FILES['data'].read())
    outfile.close() 
    
    config_file=tempfile.NamedTemporaryFile(prefix='nmtk_config_',
                                            delete=False)
    config_file.write(json.dumps(request.NMTK.config))
    config_file.close()
    # This is here because the celery job isn't running as the www-data user
    # and as a result has issues reading the tempfile that is created.
    # Once deployed (and all run as the same user) we can probably dispense
    # with this.
    for filename in [outfile.name, config_file.name]:
        os.chmod(filename,stat.S_IROTH|stat.S_IREAD|stat.S_IWRITE)
    # We should now be able to load the configuration and process the 
    # job...
    ret = tasks.performModel.delay(data_file=outfile.name, 
                                   job_config=config_file.name, 
                                   tool_config=config,
                                   client=request.NMTK.client,
                                   perform_exp=perform_exp)
    return HttpResponse('OK')
        
@csrf_exempt
@decorators.nmtk        
def updateToolConfig(request, tool_name):
    '''
    A simple function that can be used to send a tool configuration up to 
    the NMTK server.  This isn't something that the NMTK framework provides,
    but it's useful with the test server - iteratively testing tools means
    that configs can change regularly, and the test server can
    alter its behaviour immediately on a config reload.
    '''
    client_config=settings.NMTK_KEYS['MN_Model']
    if tool_name.lower() == 'ols':
        config=generateOLSToolConfiguration(request).content
    elif tool_name.lower() =='binomial':
        config=generateBinomialToolConfiguration(request).content
    response=request.NMTK.client.updateConfig(config)
    return HttpResponse(response)
    
    
    
    
    