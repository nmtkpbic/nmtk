#!/usr/bin/env python
# Nonmotorized Toolkit
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
from django.http import HttpResponse, Http404
from django.core.urlresolvers import reverse
from NMTK_apps import urls
from NMTK_apps import decorators
from django.core.exceptions import SuspiciousOperation, PermissionDenied
import json
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from importlib import import_module
import os
import stat
import tempfile
import logging
logger = logging.getLogger(__name__)

# @csrf_exempt


def tool_base_view(request, tool_name, subtool_name=None):
    '''
    Just return the URL for a tool.
    '''
    if not subtool_name:
        return HttpResponse(tool_name)
    else:
        return HttpResponse('{0}/{1}'.format(tool_name, subtool_name))


@csrf_exempt
def generateToolConfiguration(request, tool_name, subtool_name=None):
    '''
    Return the JSON tool configuration file for tool_name/subtool_name
    Use a generator function if available, otherwise load the JSON
    file from the Django templates folder for the tool.
    '''
    tool = subtool_name or 'tool_config'
    logger.debug("Generating tool configuration for %s" % (tool_name,))
    try:
        module = "%s.tool_configs" % (tool_name,)
        config = import_module(".tool_configs", tool_name)
    except Exception as e:
        logger.debug(
            "Could not import tool_configs from module %s" %
            (module,))
        raise Http404
    try:
        # Create a Python dictionary for toolconfig
        if hasattr(config, "generateToolConfiguration"):
            # If available, call a function to generate toolconfig
            logger.debug(
                "Using function to generate config: %s (%s)" %
                (tool_name, tool))
            toolconfig = config.generateToolConfiguration(
                tool_name, subtool_name)
        else:
            # Otherwise, pull toolconfig from a JSON file in the
            # Django templates folder for the tool.
            config_file = '{0}.json'.format(tool)
            logger.debug(
                "Using Django template to generate config: %s" %
                (config_file,))
            try:
                toolconfig = json.loads(
                    render_to_string(
                        os.path.join(
                            tool_name,
                            config_file)))
            except ValueError as e:
                toolconfig = {}
                logger.exception(
                    'Failed to parse config: %s - invalid tool config?', os.path.join(
                        tool_name,
                        config_file))
    except Exception as e:
        logger.exception('Failed to get config for tool!')
        raise Http404

    # Add in the host and route data for this running instance
    kwargs = {'tool_name': tool_name,
              'subtool_name': subtool_name}
    if not subtool_name:
        del kwargs['subtool_name']
    toolconfig['host'] = {'url': request.build_absolute_uri('/'),
                          'route': reverse('tool_base', kwargs=kwargs)}

    # Return the configuration as JSON text
    return HttpResponse(json.dumps(toolconfig),
                        content_type='application/json')


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
    result = []
    logger.debug('NMTK_TOOL_APPS = ' + str(settings.NMTK_TOOL_APPS))
    for app in settings.NMTK_TOOL_APPS:
        try:
            config = import_module(".tool_configs", app)
            logger.debug('Located tool config for %s (%s)', app, config)
            subtools = getattr(config, 'tools', [])
            if subtools:  # if at least one name for a subtool is in the list
                for tool in subtools:
                    result.append(
                        reverse(
                            'tool_base',
                            kwargs={
                                'tool_name': app,
                                'subtool_name': tool}))
            else:  # either don't have (sub)tools list, or it's empty
                result.append(reverse('tool_base', kwargs={'tool_name': app}))
        except Exception as e:
            logger.exception('App %s has no tool config', app)
    logger.debug("Tool list is %s", result)
    return HttpResponse(json.dumps(result),
                        content_type='application/json')


@csrf_exempt
@decorators.nmtk  # Valid request required to run the model.
def runModel(request, tool_name, subtool_name=None):
    '''
    This view will receive a request to run a tool and perform all the
    relevant security/content checks.  It then calls the tool processing
    function via a celery task.  This allows us to immediately return
    a response to the client, and then the processing task can update the
    status to the NMTK server.
    '''

    try:
        config = json.loads(
            generateToolConfiguration(
                request,
                tool_name,
                subtool_name).content)
    except:
        raise Http404

    # Grab the uploaded files and store them on the file system, preserve
    # the extension, since OGR might need it to determine the driver
    # to use to read the file.

    # Parse the configuration provided by the tool.
    try:
        config = json.loads(request.FILES['config'].read())
        logger.debug('Job Config is: %s', config)
        request.FILES['config'].seek(0)
    except Exception as e:
        logger.exception('Job configuration not parsable (%s)!', e)
        raise SuspiciousOperation('Job configuration is not parsable!')

    input_files = {}
    # Grab all the files that were passed to the tool and
    # store them in temp storage.  input_files will contain
    # the namespace --> filename mappings.
    for namespace in request.FILES.keys():
        filedata = request.FILES[namespace]
        extension = os.path.splitext(filedata.name)[1]
        outfile = tempfile.NamedTemporaryFile(suffix=extension,
                                              prefix='nmtk_upload_',
                                              delete=False)
        outfile.write(request.FILES[namespace].read())
        outfile.close()
        input_files[namespace] = (outfile.name, filedata.content_type)
    logger.debug('Input files are: %s', input_files)

    # This is here because the celery job isn't running as the www-data user
    # and as a result has issues reading the tempfile that is created.

    for namespace, filedata in input_files.iteritems():
        os.chmod(filedata[0], stat.S_IROTH | stat.S_IREAD | stat.S_IWRITE)
    # We should now be able to load the configuration and process the
    # job...

    # here we call the task for the model.
    module_name = "{0}.tasks".format(tool_name)
    tasks = import_module(".tasks", tool_name)
    logger.debug('Task module (%s) is %s (%s)', module_name,
                 tasks.__name__, tasks.__file__)
    if hasattr(tasks, 'performModel'):
        ret = tasks.performModel.delay(input_files=input_files,
                                       tool_config=config,
                                       client=request.NMTK.client,
                                       subtool_name=subtool_name)
        return HttpResponse('OK')
    else:
        raise SuspiciousOperation('Invalid tool!')
