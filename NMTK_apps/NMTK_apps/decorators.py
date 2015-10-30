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
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
from django.conf import settings
from django.core.exceptions import PermissionDenied, SuspiciousOperation
import hmac
import os
import json
import hashlib
import logging
from NMTK_apps.helpers import server_api
from collections import namedtuple
logger = logging.getLogger(__name__)
NMTKConfig = namedtuple('NMTK', ['client', 'job_id', 'tool_id', 'server_url',
                                 'config'])


def nmtk(func):
    '''
    This decorator is used to add the NMTK attribute to the HttpRequest
    object, it requires that authentication information be provided
    by the NMTK server making the request, and appropriately adds on
    all the NMTK related "stuff", including an instance of the NMTK
    server API.
    '''
    def wrapped(request, *pargs, **kwargs):
        if 'config' not in request.FILES:
            logger.error('Request does not contain config file')
            raise PermissionDenied
        config = request.FILES['config'].read()
        request.FILES['config'].seek(0)
        try:
            configobj = json.loads(config)
        except:
            logger.exception('Failed to parse JSON config object (%s)', config)
            raise SuspiciousOperation('Invalid config')
        # Ensure that the config object has a job/tool_server_id value.
        if ('job' not in configobj or
                'tool_server_id' not in configobj['job']):
            logger.error(
                'Config object lacks appropriate job data, permission denied.')
            raise PermissionDenied
        tool_server_id = configobj['job']['tool_server_id']
        location = os.path.join(settings.FILES_PATH, 'NMTK_tools', 'servers',
                                '{0}.config'.format(tool_server_id))
        if not os.path.exists(location):
            logger.error('Did not find tool_server_id of %s',
                         tool_server_id)
            raise PermissionDenied
        else:
            with open(location) as server_config_file:
                server_data = json.load(server_config_file)
        job_id = configobj['job'].get('job_id')

#         server_data = settings.NMTK_SERVERS.get(tool_server_id)
        if not server_data:
            logger.error('Did not find tool_server_id of %s',
                         tool_server_id)
            raise PermissionDenied
        digest = hmac.new(
            str(server_data['shared_secret']),
            config,
            hashlib.sha1).hexdigest()
        auth = request.META.get('HTTP_AUTHORIZATION')
        if not auth:
            logger.error('Failed to provide Authorization header')
            raise PermissionDenied
        elif auth != digest:
            logger.error('Authorization failed, received %s, computed %s',
                         auth, digest)
            raise PermissionDenied
        # At this point, we've validated the payload.
        job_id = configobj['job'].get('job_id')
        api = server_api.NMTKClient(server_data['url'],
                                    tool_server_id,
                                    server_data['shared_secret'],
                                    job_id,
                                    verify_ssl=server_data.get('verify_ssl', True))
        request.NMTK = NMTKConfig(api,
                                  "%s" % (job_id,),
                                  "%s" % (tool_server_id,),
                                  server_data['url'],
                                  configobj)
        return func(request, *pargs, **kwargs)
    return wrapped
