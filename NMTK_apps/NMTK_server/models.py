from django.db import models
from uuidfield import UUIDField
from jsonfield import JSONField
from random import choice
from django.conf import settings
import os
from django.core.files.storage import FileSystemStorage

fs = FileSystemStorage(location=os.path.join(settings.BASE_PATH,'..', 'NMTK_server', 'files'))


class ToolServer(models.Model):
    name=models.CharField(max_length=64,
                          help_text='A descriptive name for this tool server.')
    tool_server_id = UUIDField(auto=True, primary_key=True)
    auth_token=models.CharField(max_length=50,
                             default=lambda: ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)]))
    remote_ip=models.IPAddressField(blank=True,null=True,
                                    help_text=('The IP where the tool resides' +
                                               ' so we can verify the request' +
                                               ' source IP as well if needed'))
    active=models.BooleanField(default=True)
    last_modified=models.DateTimeField(auto_now=True)
    server_url=models.URLField()
    
# Create your models here.       
class Tool(models.Model):
    '''
    For the NMTK server, the tool model will contain information about registered
    tools.
    '''
    name=models.CharField(max_length=64,
                          help_text='The name of the tool')
    tool_path=models.CharField(max_length=64,
                               help_text='The URL path for the tool')
    tool_server=models.ForeignKey(ToolServer)
    active=models.BooleanField(default=True)
    last_modified=models.DateTimeField(auto_now=True)
    @property
    def analyze_url(self):
        return "%s/%s/analyze" % (self.tool_server.server_url, 
                                  self.tool_path)
    @property
    def config_url(self):
        return "%s/%s/config" % (self.tool_server.server_url,
                                 self.tool_path)    
    
    def __unicode__(self):
        return self.name
    
class ToolConfig(models.Model):
    '''
    Each tool has a single configuration, which is stored as a configuration
    object (json encoded structure.)
    '''
    tool=models.OneToOneField(Tool)
    json_config=JSONField()
    
class Job(models.Model):
    STATUS_CHOICES=(('U','Not Yet Configured'),
                    ('A','Active',),
                    ('F','Failed',),
                    ('C','Complete'),
                    )
    def __init__(self, *args, **kwargs):
        super(Job, self).__init__(*args, **kwargs)
        self._old_status=self.status
    job_id=UUIDField(auto=True, primary_key=True)
    tool=models.ForeignKey(Tool)
    create_ts=models.DateTimeField(auto_now_add=True)
    status=models.CharField(max_length=32, choices=STATUS_CHOICES, default='U')
    file=models.FileField(storage=fs, upload_to=lambda instance, filename: 'data_files/%s.geojson' % (instance.job_id,))
    results=models.FileField(storage=fs, upload_to=lambda instance, filename: 'results/%s.results' % (instance.job_id,),
                             blank=True, null=True)
    # This will contain the config data to be sent along with the job, in 
    # a JSON format of a multi-post operation.
    config=JSONField(null=True)
    
class JobStatus(models.Model):
    job=models.ForeignKey(Job)
    timestamp=models.DateTimeField(auto_now_add=True)
    message=models.CharField(max_length=1024)
    class Meta:
        ordering=['-timestamp']
    