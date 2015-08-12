'''
Decorators related to authentication for NMTK stuff
'''
from NMTK_server import models
from collections import namedtuple
from django.core.exceptions import PermissionDenied
import hmac
import json
import hashlib
import collections
import logging
logger = logging.getLogger(__name__)


def requireValidAuthToken(wrapped_function):
    '''
    Verify that there is a valid authentication token provided in the
    auth_key.  If there is one, add the Tool record to the
    HttpRequest object so it can be referenced later (if needed.)
    If there is *not* one, or we don't recognize a valid token,
    then we need to raise a PermissionDenied exception.

    The expectation here is that the auth_key will contain the shared
    public key between the server and client or the job id.

    Normally, NMTK doesn't support the public key of the tool, but we
    stick it in here so we can do config updates.
    '''
    def function_wrapper(request, *pargs, **kwargs):
        '''
        Generate an HMAC signature for the entire payload using the
        private key of the application.  This'll go in the
        HTTP protocol standard authorization header.
        '''
        logger.debug('Got a request: %s', request.FILES)
        if 'config' in request.FILES:
            config = request.FILES['config'].read()
            request.FILES['config'].seek(0)
            config_obj = json.loads(config)
            server_id = config_obj['job'].get('tool_server_id')
            job_id = config_obj['job'].get('job_id')
            logger.debug('Processing request tool_server_id %s, job_id %s',
                         server_id, job_id)
            logger.debug('Configuration object is %s', config_obj)
            try:
                jobs = models.Job.objects.filter(job_id=job_id)
                if len(jobs) == 1:
                    job = jobs[0]
                    request.NMTK_JOB = job
                    request.NMTK_TOOL = job.tool
                    request.NMTK = job.tool.tool_server
                else:
                    logger.debug('Job id of %s not found', job_id)
                    tool = models.ToolServer.objects.get(tool_id=server_id)
                    request.NMTK = tool
                if hasattr(request, 'NMTK'):
                    logger.debug('Private key is %r', request.NMTK.auth_token)
                    digest_maker = hmac.new(str(request.NMTK.auth_token),
                                            config,
                                            hashlib.sha1)
                    digest = digest_maker.hexdigest()
                    if request.META['HTTP_AUTHORIZATION'] == digest:
                        logger.debug(
                            'HTTP_AUTHORIZATION value matched expected digest.')
                        return wrapped_function(request, *pargs, **kwargs)
                    else:
                        logger.error(
                            'Computed signature was %s, received %s',
                            digest,
                            request.META['HTTP_AUTHORIZATION'])
            except:
                logger.exception('Error processing request')
        raise PermissionDenied
    return function_wrapper


def requireValidJobId(wrapped_function):
    '''
    Just verify that request.NMTK_JOB exists...
    '''
    def function_wrapper(request, *pargs, **kwargs):
        logger.debug('Checking to ensure the job id is valid.')
        if getattr(request, 'NMTK_JOB'):
            return wrapped_function(request, *pargs, **kwargs)
        raise PermissionDenied
    return function_wrapper
