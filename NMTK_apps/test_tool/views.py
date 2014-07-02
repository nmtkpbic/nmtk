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
from test_tool import tasks
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
    Simply take the configuration for a tool from the tool_configs hash,
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
    return HttpResponse(json.dumps(config),
                        content_type='application/json')

@csrf_exempt
def generateDocs(request, tool_name):
    '''
    We put the HTML for documentation in the docs/ directory, this just serves 
    up those files to the user.
    '''
    return render(request, 'test_tool/docs/%s.html' % (tool_name.lower(),),)

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

    config=json.loads(generateToolConfiguration(request, tool_name).content)
    # Grab the uploaded files and store them on the file system, preserve
    # the extension, since OGR might need it to determine the driver
    # to use to read the file. 
    
    # So we expect there to be two keys for the uploaded files here,
    # config - for the config object
    # data - for the data object.
    logger.debug('Keys in request.FILES are %s', request.FILES)
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
    # This is here because the celery job may not be running as the www-data user
    # and as a result may have issues reading the tempfile that is created.
    # Once deployed (and all run as the same user) we can probably dispense
    # with this.
    for filename in [outfile.name, config_file.name]:
        os.chmod(filename,stat.S_IROTH|stat.S_IREAD|stat.S_IWRITE)
    # We should now be able to load the configuration and process the 
    # job...
    ret = tasks.performModel.delay(data_file=outfile.name, 
                                   job_setup=config_file.name, 
                                   tool_config=config,
                                   client=request.NMTK.client)
    return HttpResponse('OK')