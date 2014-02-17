# Create your views here.
import json
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import SuspiciousOperation, PermissionDenied
from django.forms.models import model_to_dict
from django.conf import settings
from NMTK_apps.helpers import  server_api
from NMTK_apps import decorators
import os
import tempfile
from SF_model import tasks
import logging
logger=logging.getLogger(__name__)
import hmac
import hashlib
import tool_configs
import os, stat

@csrf_exempt
def toolBase(request, tool_name):
    '''
    This is the "base url" for the tool.  Generally, it doesn't do anything
    but there are several spots where we need to output it (for example, in 
    config) so this particular view is just here for the reverse-urlpattern.
    '''
    if not tool_configs.configs.has_key(tool_name):
        raise Http404
    return HttpResponse('%s' % (tool_name,))

@csrf_exempt
def generateToolConfiguration(request, tool_name):
    '''
    Simply take the configuration for a tool from the tool_configs table,
    substitute in any specific URL parameters, then return the config
    as a json object to the requestor.
    '''
    if not tool_configs.configs.has_key(tool_name):
        raise Http404
    config=tool_configs.configs[tool_name]
    # Add in the host and route data...
    config['host']={'url': request.build_absolute_uri('/'),
                    'route': reverse('tool_base',  
                                     kwargs={'tool_name': tool_name}) }
#     for k in config['documentation']['links']:
#         config['documentation']['links'][k]=request.build_absolute_uri('/') + \
#                                             reverse('SF_Documentation',
#                                                     kwargs={'tool_name': tool_name})
    return HttpResponse(json.dumps(config),
                        content_type='application/json')

@csrf_exempt
def generateDocs(request, tool_name):
    '''
    We put the HTML for documentation in the docs/ directory, this just serves 
    up those files to the user.
    '''
    if not hasattr(tool_configs, tool_name):
        raise Http404
    return render(request, 'SF_model/docs/%s.html' % (tool_name.lower(),),)

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
    if not tool_configs.configs.has_key(tool_name):
        raise Http404
    logger.debug('Received request for processing!')

    config=json.loads(generateToolConfiguration(request, tool_name).content)
    # Grab the uploaded files and store them on the file system, preserve
    # the extension, since OGR might need it to determine the driver
    # to use to read the file. 
    
    # Parse the configuration provided by the tool.
    try:
        config=json.loads(request.FILES['config'].read())
        logger.debug('Job Config is: %s', config)
        request.FILES['config'].seek(0)
    except Exception, e:
        logger.exception('Job configuration not parseable (%s)!', e)
        raise SuspiciousOperation('Job configuration is not parseable!')
    
    input_files={}
    # Grab all the files that were passed to the tool and 
    # store them in temp storage.  input_files will contain
    # the namespace --> filename mappings.
    for namespace in request.FILES.keys():
        filedata=request.FILES[namespace]
        extension=os.path.splitext(filedata.name)[1]
        outfile=tempfile.NamedTemporaryFile(suffix=extension, 
                                            prefix='nmtk_upload_',
                                            delete=False)
        outfile.write(request.FILES[namespace].read())
        outfile.close() 
        input_files[namespace]=(outfile.name, filedata.content_type)
    logger.debug('Input files are: %s', input_files)
    
#     config_file=tempfile.NamedTemporaryFile(prefix='nmtk_config_',
#                                             delete=False)
#     config_file.write(json.dumps(request.NMTK.config))
#     config_file.close()
    # This is here because the celery job isn't running as the www-data user
    # and as a result has issues reading the tempfile that is created.
    # Once deployed (and all run as the same user) we can probably dispense
    # with this.
    for namespace, filedata in input_files.iteritems():
        os.chmod(filedata[0],stat.S_IROTH|stat.S_IREAD|stat.S_IWRITE)
    # We should now be able to load the configuration and process the 
    # job...
    ret = tasks.performModel.delay(input_files=input_files,
                                   tool_config=config,
                                   client=request.NMTK.client)
    return HttpResponse('OK')
        
    
    
    
    
    