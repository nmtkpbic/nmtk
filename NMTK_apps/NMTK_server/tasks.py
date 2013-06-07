from celery.task import task
import json
import decimal
import requests
import hmac
import hashlib
import uuid
from datetime import datetime
import logging
from django.core.serializers.json import DjangoJSONEncoder
logger=logging.getLogger(__name__)


@task(ignore_result=False)
def submitJob(job):
    '''
    Whenever a job status is set to active in the database, the 
    signal attached to the model causes the job to be submitted.
    This causes this task (a celery task) to run, and submit
    the job to the tool.
    '''
    # Get a logger to log status for this task.
    logger=submitJob.get_logger()
    logger.debug('Submitting job %s to tool %s for processing', job.pk,
                 job.tool)
    
    configuration={'analysis settings': job.config }
    configuration['job']= {'tool_server_id': "%s" % (job.tool.tool_server.tool_server_id,),
                           'job_id': str(job.job_id),
                           'timestamp': datetime.now().isoformat() }
    config_data=json.dumps(configuration, cls=DjangoJSONEncoder)
    digest_maker =hmac.new(str(job.tool.tool_server.auth_token), 
                           config_data, 
                           hashlib.sha1)
    digest=digest_maker.hexdigest()
    
    files= {'config': ('config', config_data),
            'data': (job.data_file.name, job.data_file.file) }
    r=requests.post(job.tool.analyze_url, files=files,
                    headers={'Authorization': digest })
    logger.debug("Submitted job to %s tool, response was %s", 
                 job.tool, r.content)
         
    
