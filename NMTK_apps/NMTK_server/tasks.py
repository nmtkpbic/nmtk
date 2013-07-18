from celery.task import task
import simplejson as json
import decimal
import requests
import hmac
import hashlib
import uuid
from django.utils import timezone
from django.conf import settings
import logging
import os
from django.core.exceptions import ObjectDoesNotExist
from NMTK_server import geo_loader
from django.core.files import File
from django.contrib.gis.geos import Polygon
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.core.mail import send_mail
#from django.core.serializers.json import DjangoJSONEncoder
logger=logging.getLogger(__name__)

@task(ignore_result=True)
def email_user_job_complete(job):
#    from NMTK_server import models
#    job=models.Job.objects.select_related('user','tool').get(pk=job_id)
    context={'job': job,
             'user': job.user,
             'tool': job.tool,
             'site': Site.objects.get_current()}
    logger.debug('Job complete (%s), sending email to %s', 
                 job.tool.name, job.user.email)
    subject=render_to_string('NMTK_server/job_finished_subject.txt',
                             context).strip().replace('\n',' ')
    message=render_to_string('NMTK_server/job_finished_message.txt',
                             context)
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL,
              [job.user.email,])

@task(ignore_result=False)
def add_toolserver(name, url, username, remote_ip=None):
    from NMTK_server import models
    try:
        user=User.objects.get(username=username)
    except Exception, e:
        raise CommandError('Username specified (%s) not found!' % 
                           username)
    m=models.ToolServer(name=name,
                        server_url=url,
                        remote_ip=remote_ip,
                        created_by=user)
    m.save()
    return m

@task(ignore_result=False)
def discover_tools(toolserver):
    from NMTK_server import models

    url="%s/index" % (toolserver.server_url) # index returns a json list of tools.
    tool_list=requests.get(url).json()
    logger.debug('Retrieved tool list of: %s', tool_list)
    for tool in tool_list:
        try:
            t=models.Tool.objects.get(tool_server=toolserver,
                                      tool_path=tool)
        except ObjectDoesNotExist:
            t=models.Tool(tool_server=toolserver,
                          name=tool)
        t.active=True
        t.tool_path=tool
        t.name=tool
        t.save()
    
    # Locate all the tools that aren't there anymore and disable them.
    for row in models.Tool.objects.exclude(tool_path__in=tool_list).filter(active=True):
        logger.debug('Disabling tool %s', row.name)
        row.active=False
        row.save()

@task(ignore_result=False)
def submitJob(job):
    '''
    Whenever a job status is set to active in the database, the 
    signal attached to the model causes the job to be submitted.
    This causes this task (a celery task) to run, and submit
    the job to the tool.
    '''
    from NMTK_server import models
    # Get a logger to log status for this task.
    logger=submitJob.get_logger()
    logger.debug('Submitting job %s to tool %s for processing', job.pk,
                 job.tool)
    
    configuration={'analysis settings': job.config }
    configuration['job']= {'tool_server_id': "%s" % (job.tool.tool_server.tool_server_id,),
                           'job_id': str(job.job_id),
                           'timestamp': timezone.now().isoformat() }
    config_data=json.dumps(configuration, use_decimal=True) #cls=DjangoJSONEncoder)
    digest_maker =hmac.new(str(job.tool.tool_server.auth_token), 
                           config_data, 
                           hashlib.sha1)
    digest=digest_maker.hexdigest()
    logger.debug('Processed file is %s', job.data_file.processed_file)
    files= {'config': ('config', config_data),
            'data': (job.data_file.processed_file.name, job.data_file.processed_file) }
    logger.debug('Files for job are %s', files)
    r=requests.post(job.tool.analyze_url, files=files,
                    headers={'Authorization': digest })
    logger.debug("Submitted job to %s tool, response was %s (%s)", 
                 job.tool, r.text, r.status_code)
    if r.status_code <> 200:
        job.status=job.TOOL_FAILED
        js=models.JobStatus(job=job,
                            message=('Tool failed to accept ' + 
                                     'job (return code %s)') % (r.status_code,))
        js.save()
        job.save()
        
    
@task(ignore_result=False)
def updateToolConfig(tool):
    from NMTK_server import models
    json_config=requests.get(tool.config_url)
    try:
        config=tool.toolconfig
    except:
        config=models.ToolConfig(tool=tool)
    config_data=json_config.json()
    config.json_config=config_data
    config.save()
    # Note: We use update here instead of save, since we want to ensure that
    # we don't call the post_save handler, which would result in
    # a recursion loop.
    logger.debug('Setting tool name to %s', config_data['info']['name'])
    models.Tool.objects.filter(pk=config.tool.pk).update(name=config_data['info']['name'])
    
         
@task(ignore_result=False)
def importDataFile(datafile):
    try:
        geoloader=geo_loader.GeoDataLoader(datafile.file.path,
                                           srid=datafile.srid)
        datafile.srid=geoloader.info.srid
        datafile.extent=Polygon.from_bbox(geoloader.info.extent)
        datafile.srs=geoloader.info.srs
        datafile.feature_count=geoloader.info.feature_count
        datafile.geom_type=geoloader.info.type
        datafile.status=datafile.IMPORTED
        datafile.processed_file=geoloader.geojson
        # Get the base name of the file (without the extension)
        # We can use that as the basis for the name of the GeoJSON file
        # that we processed.
        name=os.path.splitext(os.path.basename(datafile.file.path))[0]
        datafile.processed_file.save('%s.geojson' % (name,),
                                     File(open(geoloader.geojson)))
    except Exception, e:
        logger.exception('Failed import process!')
        datafile.status=datafile.IMPORT_FAILED
        datafile.status_message="%s" % (e,)
    datafile.save()
    
    