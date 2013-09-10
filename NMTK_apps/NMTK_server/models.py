from django.contrib.gis.db import models
from uuidfield import UUIDField
from jsonfield import JSONField
from random import choice
from django.conf import settings
from django.contrib.auth.models import User
import os
from django.core.urlresolvers import reverse
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.utils.safestring import mark_safe
from osgeo import ogr
from NMTK_server import tasks
from NMTK_server import signals
import logging
logger=logging.getLogger(__name__)


class NMTKDataFileSystemStorage(FileSystemStorage):
    def url(self, name):
        raise NotImplementedError
        return reverse('NMTK_server.download_datafile',
                       kwargs={'file_id': name})
        
class NMTKGeoJSONFileSystemStorage(FileSystemStorage):
    def url(self, name):
        raise NotImplementedError
        return reverse('NMTK_server.download_geojson_datafile',
                       kwargs={'file_id': name})
        
class NMTKResultsFileSystemStorage(FileSystemStorage):
    '''
    Kind of hokey here, but we will use the filename to determine the job
    id, and thereby figure out how to generate the download link.
    '''
#     def url(self, name):
# #        raise NotImplementedError
#         return reverse('downloadResults',
#                        kwargs={'job_id': name.rsplit('/',2)[-1].split('.')[0]})
        
location=os.path.join(settings.FILES_PATH, 'NMTK_server', 'files')
fs = NMTKDataFileSystemStorage(location=location)
fs_geojson = NMTKGeoJSONFileSystemStorage(location=location)
fs_results = NMTKResultsFileSystemStorage(location=location)

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
    date_created=models.DateTimeField(auto_now_add=True)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL)
    objects=models.GeoManager()
    def __str__(self):
        return "%s" % (self.name,)
    
    def save(self, *args, **kwargs):
        '''
        Whenever a toolserver record is saved (and it's not a new record) we will
        go out and discover its tools.
        '''
        result=super(ToolServer, self).save(*args, **kwargs)
        logger.debug('Detected a save of the ToolServer model, adding/updating tools.')
        tasks.discover_tools.delay(self)
        return result
    
    class Meta:
       
        verbose_name='Tool Server'
        verbose_name_plural='Tool Servers'
    
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
    objects=models.GeoManager()

    @property
    def analyze_url(self):
        return "%s/%s/analyze" % (self.tool_server.server_url, 
                                  self.tool_path)
    @property
    def config_url(self):
        return "%s/%s/config" % (self.tool_server.server_url,
                                 self.tool_path)    
        
    def save(self, *args, **kwargs):
        result=super(Tool, self).save(*args, **kwargs)
        if self.active:
            logger.debug('Detected a save of the Tool model, updating configs.')
            tasks.updateToolConfig.delay(self)
        return result
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name='Tool'
        verbose_name_plural='Tools'
    
class ToolConfig(models.Model):
    '''
    Each tool has a single configuration, which is stored as a configuration
    object (json encoded structure.)
    '''
    tool=models.OneToOneField(Tool)
    json_config=JSONField()
    objects=models.GeoManager()

    class Meta:
        verbose_name='Tool Configuration'
        verbose_name_plural='Tool Configurations'
        
class Job(models.Model):
    UNCONFIGURED='U'
    ACTIVE='A'
    FAILED='F'
    COMPLETE='C'
    TOOL_FAILED='TF'
    STATUS_CHOICES=((UNCONFIGURED,'Configuration Pending'),
                    (ACTIVE,'Active',),
                    (FAILED,'Failed',),
                    (TOOL_FAILED,'Tool Failed to Accept Job',),
                    (COMPLETE,'Complete'),
                    )
    
    def __init__(self, *args, **kwargs):
        super(Job, self).__init__(*args, **kwargs)
        self._old_status=self.status
        self._old_data_file=self.data_file if hasattr(self,'data_file') else None
        self._old_tool=self.tool if hasattr(self,'tool') else None
    job_id=UUIDField(auto=True, primary_key=True)
    tool=models.ForeignKey(Tool, on_delete=models.PROTECT)
    date_created=models.DateTimeField(auto_now_add=True)
    status=models.CharField(max_length=32, choices=STATUS_CHOICES, default=UNCONFIGURED)
    #file=models.FileField(storage=fs, upload_to=lambda instance, filename: 'data_files/%s.geojson' % (instance.job_id,))
    data_file=models.ForeignKey('DataFile', null=False, related_name='data_file_job',
                                blank=False, on_delete=models.PROTECT)
    results=models.FileField(storage=fs_results, 
                             upload_to=lambda instance, filename: '%s/results/%s.results' % (instance.user.pk,
                                                                                             instance.pk,),
                             blank=True, null=True)
    sqlite_db=models.FileField(storage=fs_results,
                                   upload_to=lambda instance, filename: '%s/results/%s.spatialite' % (instance.user.pk,
                                                                                                      instance.pk,),
                                   blank=True, null=True)
    mapfile=models.FileField(storage=fs_results,
                             upload_to=lambda instance, filename: '%s/results/%s.map' % (instance.user.pk,
                                                                                         instance.pk,),
                             blank=True, null=True)
    legendgraphic=models.FileField(storage=fs_results,
                                   upload_to=lambda instance, filename: '%s/results/%s_legend.png' % (instance.user.pk,
                                                                                                      instance.pk))
    model=models.FileField(storage=fs_results,
                           upload_to=lambda instance, filename: '%s/results/%s.py' % (instance.user.pk,
                                                                                      instance.pk,),
                           blank=True, null=True)
    # This will contain the config data to be sent along with the job, in 
    # a JSON format of a multi-post operation.
    config=JSONField(null=True)
    description=models.CharField(max_length=2048, null=True, blank=True,
                                 help_text='A free-form description of this job')
    # The user that created the job (used to restrict who can view the job.)
    user=models.ForeignKey(settings.AUTH_USER_MODEL, null=False)
    email=models.BooleanField(default=False, help_text='Email user upon job completion')
    objects=models.GeoManager()

    def delete(self):
        '''
        Ensure files are deleted when the model instance is removed.
        '''
        r=super(Job, self).delete()
        for field in ['results','sqlite_db','mapfile', 'model', 'legendgraphic']:
            if getattr(self, field, None):
                os.unlink(getattr(self, field).path)
                if field == 'model':
                    compiled_module="{0}s".format(self.model.path)
                    if os.path.exists(compiled_module):
                        os.unlink(compiled_module)
        return r
    
    @property
    def results_link(self):
        return reverse('viewResults', kwargs={'job_id': self.job_id})
    
    def __str__(self):
        return "%s for %s" % (self.pk, self.user.username)

    def save(self, *args, **kwargs):    
        '''
        Rather than have the view code have to submit the job, we'll just 
        monitor the job table.  Whenever a job gets configured, the
        state change from unconfigured to configured will trigger 
        sending the job to the client - so we have a single entry point
        for sending jobs to the client.
        
        In the interest of speed, the job execution work (which might take 
        some time to submit) is passed off as a celery task, so the client gets
        it's response(s) back immediately.
        '''
        result=super(Job, self).save(*args, **kwargs)
        if self._old_status == 'U' and self.status == 'A':
            logger.debug('Detected a state change from Unconfigured to ' + 
                         'Active for job (%s.)', self.pk)
            logger.debug('Sending job to tool for processing.')
            # Submit the task to the client, passing in the job identifier.
            tasks.submitJob.delay(self)
        if (self.email and self._old_status <> self.status and
            self.status in (self.FAILED, self.COMPLETE, self.TOOL_FAILED,)):
            tasks.email_user_job_complete.delay(self)
        if (self.results and not self.sqlite_db):
            logger.debug('Generating SQLITE database for results management (%s)',
                         self.pk)
            # Generate the spatialite database for performance.
            tasks.generate_sqlite_database(self)
            logger.debug('Saving %s,%s,%s,%s', 
                         self.results, self.sqlite_db, self.mapfile,
                         self.model)
            super(Job, self).save()
        return result
    
    class Meta:
        ordering=['-date_created']
        verbose_name='Job'
        verbose_name_plural='Jobs'

  
class DataFile(models.Model):
    PENDING=1
    PROCESSING=2
    IMPORTED=3
    IMPORT_FAILED=4
    
    STATUSES=((PENDING,'Import Pending',),
              (PROCESSING,'File submitted for processing',),
              (IMPORTED,'Import Complete',),
              (IMPORT_FAILED, 'Import Failed',),
              )
    # The supported geometry types
    GEOM_TYPES=((ogr.wkbPoint, 'POINT'),
                (ogr.wkbGeometryCollection, 'GEOMETRYCOLLECTION'),
                (ogr.wkbLineString, 'LINESTRING'),
                (ogr.wkbMultiPoint, 'MULTIPOINT'),
                (ogr.wkbMultiPolygon, 'MULTIPOLYGON'),
                (ogr.wkbPolygon, 'POLYGON'),
                (ogr.wkbMultiLineString, 'MULTILINESTRING'),
                )
    file=models.FileField(storage=fs, 
                          upload_to=lambda instance, filename: '%s/data_files/%s' % (instance.user.pk, filename,))
    processed_file=models.FileField(storage=fs_geojson, 
                                    upload_to=lambda instance, filename: '%s/data_files/converted/%s' % (instance.user.pk, filename,))
    name=models.CharField(max_length=64)
    status=models.IntegerField(choices=STATUSES, default=PENDING)
    status_message=models.TextField(blank=True, null=True)
    srid=models.IntegerField(null=True, blank=True)
    srs=models.TextField(null=True, blank=True)
    feature_count=models.IntegerField(null=True, blank=True)
    extent=models.PolygonField(srid=4326, null=True, blank=True)  
    geom_type=models.IntegerField(choices=GEOM_TYPES, blank=True, null=True)                                                                                                                                   
    description=models.TextField(null=True, blank=True)
    content_type=models.CharField(max_length=128)
    date_created=models.DateTimeField(auto_now_add=True)
    user=models.ForeignKey(settings.AUTH_USER_MODEL, null=False)
    fields=JSONField(null=True, blank=True)
    deleted=models.BooleanField(default=False)
    job=models.ForeignKey(Job, null=True, blank=True, related_name='source_job')
    objects=models.GeoManager()
    
#    @property
#    def url(self):
#        if self.file:
#            return reverse('api_datafile_download_detail', 
#                           kwargs={'pk': self.pk,}) 
#        else:
#            return ''
    
#    @property
#    def geojson_url(self):
#        if self.processed_file:
#            return reverse('NMTK_server.download_geojson_datafile', 
#                           kwargs={'file_id': self.pk})
#        else:
#            return ''
    
    @property
    def geojson_name(self):
        return '%s.geojson' % (os.path.splitext(self.name)[0],)
    
    def save(self, *args, **kwargs):
        '''
        Default is pending, but we update that to processing on save - this
        prevents multiple jobs from being submitted.
        '''
        import_datafile=False
        if self.status==self.PENDING:
            import_datafile=True
            self.status=self.PROCESSING
        result=super(DataFile, self).save(*args, **kwargs)
        if import_datafile:
            '''
            If the file was just uploaded (status PENDING) then we kick off
            the job to import the file (and set the status to PROCESSING)
            '''
            logger.debug('Dispatching task for %s', self.pk)
            tasks.importDataFile.delay(self)
        return result
        
    def __str__(self):
        return '%s' % (self.name,)
    
    class Meta:
        ordering=['-date_created']
        verbose_name='Data File'
        verbose_name_plural='Data Files'
    
class JobStatus(models.Model):
    '''
    This model holds status updates that are returned by the tool.  It can
    probably be removed at some point after the job completes (or at least
    all but the most recent one can be removed.)
    '''
    job=models.ForeignKey(Job)
    timestamp=models.DateTimeField(auto_now_add=True)
    message=models.CharField(max_length=1024)
    objects=models.GeoManager()
    class Meta:
        ordering=['job__pk','-timestamp']
        verbose_name='Job Status'
        verbose_name_plural='Job Status'
    
class Feedback(models.Model):
    CHOICES=('No Opinion', 'Works', 'Needs Help', 'No Way');
    CHOICES=zip(CHOICES, CHOICES);
    date_created=models.DateTimeField(auto_now_add=True)
    user=models.ForeignKey(settings.AUTH_USER_MODEL, null=False)
    uri=models.CharField(max_length=255, null=False, blank=False)
    comments=models.TextField()
    transparency=models.CharField(max_length=16, null=True, choices=CHOICES)
    functionality=models.CharField(max_length=16, null=True, choices=CHOICES)
    usability=models.CharField(max_length=16, null=True, choices=CHOICES)
    performance=models.CharField(max_length=16, null=True, choices=CHOICES)
    class Meta:
        ordering=['-date_created']
        verbose_name='Feedback'
        verbose_name_plural='Feedback Items'


class UserPreference(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL, null=False)
    divs=models.CharField(null=True, blank=True, max_length=1024,
                          help_text='A JSON list of divs that are "enabled" in the UI')
    class Meta:
        verbose_name='User Preference'
        verbose_name_plural='User Preferences'
    