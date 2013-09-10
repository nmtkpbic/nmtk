from django.http import HttpResponse, HttpResponseBadRequest
import subprocess
from django.conf import settings
import djpaste
import logging
import os
logger=logging.getLogger(__name__)

def handleWMSRequest(request, job):
    if request.GET['REQUEST'].lower() == 'getlegendgraphic':
        response=HttpResponse(job.legendgraphic,content_type='image/png')
        return response
    try:
        # Create the app to call mapserver.
        app=djpaste.CGIApplication(global_conf=None, 
                                   script=settings.MAPSERV_PATH,
                                   include_os_environ=True,
                                   query_string=request.META['QUERY_STRING'],
                                   )
        environ=request.META.copy()
        environ['MS_MAPFILE']=str(job.mapfile.path)
        return app(request, environ)
    except djpaste.CGIError, e:
        logger.exception(e)
        return HttpResponseBadRequest()
    