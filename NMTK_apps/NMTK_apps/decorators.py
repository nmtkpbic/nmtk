from django.conf import settings
from django.core.exceptions import PermissionDenied, SuspiciousOperation
import hmac
import json
import hashlib
import logging
from NMTK_apps.helpers import server_api
from collections import namedtuple
logger=logging.getLogger(__name__)
NMTKConfig=namedtuple('NMTK', ['client','job_id','tool_id','server_url',
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
        if not request.FILES.has_key('config'):
            logger.error('Request does not contain config file')
            raise PermissionDenied
        config=request.FILES['config'].read()
        request.FILES['config'].seek(0)
        try:
            configobj=json.loads(config)
        except:
            logger.exception('Failed to parse JSON config object (%s)', config)
            raise SuspiciousOperation('Invalid config')
        # Ensure that the config object has a job/tool_server_id value.
        if (not configobj.has_key('job') or 
            not configobj['job'].has_key('tool_server_id')):
            logger.error('Config object lacks appropriate job data, permission denied.')
            raise PermissionDenied
        tool_server_id=configobj['job']['tool_server_id']
        job_id=configobj['job'].get('job_id')
        server_data=settings.NMTK_SERVERS.get(tool_server_id)
        if not server_data:
            logger.error('Did not find tool_server_id of %s', 
                         tool_server_id)
            raise PermissionDenied
        digest=hmac.new(server_data['secret'], config, hashlib.sha1).hexdigest()
        auth=request.META.get('HTTP_AUTHORIZATION')
        if not auth:
            logger.error('Failed to provide Authorization header')
            raise PermissionDenied
        elif auth <> digest:
            logger.error('Authorization failed, received %s, computed %s',
                         auth, digest)
            raise PermissionDenied
        # At this point, we've validated the payload.
        job_id=configobj['job'].get('job_id')
        api=server_api.NMTKClient(server_data['url'], 
                                  tool_server_id,
                                  server_data['secret'], 
                                  job_id)
        request.NMTK=NMTKConfig(api, 
                                "%s" % (job_id,), 
                                "%s" % (tool_server_id,), 
                                server_data['url'],
                                configobj)
        return func(request, *pargs, **kwargs)
    return wrapped