from celery.task import task
import simplejson as json
import decimal
import requests
import urlparse
import hmac
import hashlib
import uuid
from django.utils import timezone
from django.conf import settings
from django.core.management.color import no_style
from django.db import connections, transaction
import logging
import os
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.gis.db.backends.spatialite.creation import SpatiaLiteCreation 
from NMTK_server.data_loaders.loaders import NMTKDataLoader
from django.core.files import File
from django.contrib.gis import geos
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands import inspectdb
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.core.files.base import ContentFile
from django.shortcuts import render
from osgeo import ogr
import imp
import math
import colorsys
from PIL import Image, ImageDraw, ImageFont
from django.contrib.gis.geos import GEOSGeometry
import tempfile

#from django.core.serializers.json import DjangoJSONEncoder
logger=logging.getLogger(__name__)

geomodel_mappings={ ogr.wkbPoint: ('models.PointField', geos.Point, 'point'),
                    ogr.wkbGeometryCollection: ('models.GeometryField', geos.GEOSGeometry, 'point'),
                    ogr.wkbLineString:  ('models.LineStringField', geos.LineString, 'line'),
                    ogr.wkbMultiPoint: ('models.MultiPointField', geos.MultiPoint,'point'),
                    ogr.wkbMultiPolygon: ('models.MultiPolygonField', geos.MultiPolygon,'polygon'),
                    ogr.wkbPolygon: ('models.PolygonField', geos.Polygon,'polygon'),
                    ogr.wkbMultiLineString: ('models.MultiLineStringField', geos.MultiLineString,'line'),
                   }
# Given a min and max value, and a value (somewhere in the middle)
# return a suitable pseudo-color to match.
def pseudocolor(val, minval=0, maxval=255):
    if minval == maxval:
        h=180
    else:
        h=float(val-minval)/(maxval-minval)*120
    g,r,b=colorsys.hsv_to_rgb(h/360,1.0,1.0)
    return int(r*255),int(g*255),int(b*255)

def generateColorRampLegendGraphic(min_text, max_text, 
                                   height=16, width=258, border=1, units=None):
    logger.debug('Units are %s', units)
    im=Image.new('RGB', (width, height), "black")
    draw=ImageDraw.Draw(im)
    start=border
    stop=height-border*2
    fixed=False
    if max_text==min_text:
        fixed=True
    for i in range(border, width-border*2):
        if not fixed:
            color="rgb({0},{1},{2})".format(*pseudocolor(i, minval=0, 
                                                         maxval=width-(border*2)))
        else:
            color="rgb({0},{1},{2})".format(*pseudocolor(0, 0, 0))
        draw.line((i, start, i, stop), fill=color)
    del draw
    
    # Generate the legend text under the image
    font=ImageFont.truetype(settings.LEGEND_FONT,12)
    
    if not fixed:
        min_text_width, min_text_height = font.getsize(min_text)
        max_text_width, max_text_height = font.getsize(max_text)
        text_height=max(min_text_height, max_text_height)
        
        final_width=max(width, max_text_width, min_text_width)
    else:
        max_text_width, text_height=font.getsize('All Features')
        final_width=max(width, max_text_width)
    # The text height, plus the space between the image and text (1px)
    total_text_height=text_height+1
    logger.debug('Total text height is now %s', total_text_height)
    if units:
        units_width, units_height=font.getsize(units)
        final_width=max(final_width, units_width)
        # Another pixel for space, then the units text
        total_text_height = total_text_height + units_height + 1
        logger.debug('Total text height is now %s (post units)', 
                     total_text_height)
    im2=Image.new('RGB', (final_width, height+total_text_height+6), "white")
    im2.paste(im, (int((final_width-width)/2),0))
    text_pos=height+1
    draw=ImageDraw.Draw(im2)
    if not fixed:
        draw.text((1, text_pos),
                  min_text,
                  "black",
                  font=font)
        draw.text((final_width-(max_text_width+1), text_pos), 
                  max_text, 
                  "black", 
                  font=font)
        if units:
            text_pos = text_pos + text_height + 1
            placement=(int(final_width/2.0-((units_width+1)/2)), text_pos)
            draw.text(placement, 
                      units, 
                      "black", 
                      font=font)
    else:
        placement=(int(final_width/2.0-((max_text_width+1)/2)), text_pos)
        draw.text(placement, 
                  'All Features', 
                  "black", 
                  font=font)
    
    del draw
    return im2

# This actually does not get done as a task - it is inline with the
# response from the tool server.
def generate_datamodel(datafile, loader):
    models_spatialite=('spatialite' == getattr(settings,'USER_MODELS_LOCATION','spatialite'))
    def propertymap(data):
        output={}
        used=[]
        c=inspectdb.Command()
        for k in data:
            att_name, params, notes=inspectdb.Command.normalize_col_name(c, k, used, False)
#             logger.debug('Field %s, %s', att_name, notes)
            used.append(att_name)    
            output[k]=att_name
#         logger.debug('Mappings are %s', output)
        return output

    try:
        if loader.is_spatial:
            spatial=True
            geom_type=loader.info.type
            model_type, geos_func, mapfile_type=geomodel_mappings[geom_type]
        else:
            spatial=False
        db_created=False
        this_model=None
        colors=[]
        model_content=['from django.contrib.gis.db import models']
        feature_id=1
        for (row, geometry) in loader:
            if not db_created:
                db_created=True
                if datafile.result_field:
                    min_result=max_result=float(row[datafile.result_field])
                
                field_map=propertymap(row.keys())
                # Create the model for this data
                model_content.append('class Results_{0}(models.Model):'.format(datafile.pk))
                # Add an auto-increment field for it (the PK)
                model_content.append('{0}nmtk_id=models.IntegerField(primary_key=True)'.format(' ' * 4))
                model_content.append('{0}nmtk_feature_id=models.IntegerField()'.format(' '*4))
                # Add an entry for each of the fields
                for orig_field, new_field in field_map.iteritems():
                    model_content.append("""{0}{1}=models.TextField(null=True, db_column='''{2}''')""".
                                         format(' '*4, new_field, orig_field))    
                if spatial:
                    model_content.append('''{0}nmtk_geometry={1}(null=True, srid=4326)'''.
                                         format(' '*4, model_type))
                model_content.append('''{0}objects=models.GeoManager()'''.format(' '*4,))
                
                model_content.append('''{0}class Meta:'''.format(' '*4,))
                model_content.append('''{0}db_table='userdata_results_{1}' '''.format(' '*8,datafile.pk))
                datafile.model.save('model.py', ContentFile('\n'.join(model_content)),
                                    save=False)
                #logger.debug('\n'.join(model_content))
                user_models=imp.load_source('%s.models' % (datafile.pk,),datafile.model.path)
                Results_model=getattr(user_models,'Results_{0}'.format(datafile.pk))
                if models_spatialite:
                    # if we are using spatialite, we need to create the 
                    # database file on disk and intiailize it.
                    datafile.sqlite_db.save('db', ContentFile(''), save=False)
                    database='%s'% (datafile.pk,)
                    settings.DATABASES[database]={'ENGINE': 'django.contrib.gis.db.backends.spatialite', 
                                                  'NAME': datafile.sqlite_db.path }
                # Must stick .model in there 'cause django doesn't like models
                # without a package.
                    connection=connections[database]
                    connection.ops.spatial_version=(3,0,1)
                    SpatiaLiteCreation(connection).load_spatialite_sql()
                    dbtype='sqlite'
                else:
                    database='default'
                    # If using PostgreSQL, then just create the model and go...
                    dbtype='postgis'
                    connection=connections[database] 
                cursor=connection.cursor()
                for statement in connection.creation.sql_create_model(Results_model, no_style())[0]:
                    #logger.debug(statement)
                    cursor.execute(statement)
                for statement in connection.creation.sql_indexes_for_model(Results_model, no_style()):
                    #logger.debug(statement)
                    cursor.execute(statement)
            
            this_row=dict((field_map[k],v) for k,v in row.iteritems())
            this_row['nmtk_id']=this_row.get('nmtk_id', feature_id)
            this_row['nmtk_feature_id']=this_row.get('nmtk_id', feature_id)
            feature_id += 1
            if spatial:
                this_row['nmtk_geometry']=geometry
            if datafile.result_field:
                try:
                    logger.debug('Row is %s', this_row)
                    min_result=min(float(this_row[datafile.result_field.lower()]), min_result)
                    max_result=max(float(this_row[datafile.result_field.lower()]), max_result)
                except Exception, e:
                    logger.exception('Result field (%s) is not a float (ignoring)', datafile.result_field)
            else:
                min_result=max_result=1
            m=Results_model(**this_row)
            m.save(using=database)
#             logger.debug('Saved model with pk of %s', m.pk)
        logger.debug('Completing transferring results to %s database %s', dbtype,datafile.pk,)
        if spatial:
            logger.debug('Spatial result generating styles (%s-%s)', min_result, max_result)
            step=math.fabs((max_result-min_result)/256)
            colors=[]
            low=min_result
            v=min_result
            while v <= max_result:
                #logger.debug('Value is now %s', v)
                r,g,b=pseudocolor(v, min_result, max_result)
                colors.append({'r': r,
                               'g': g,
                               'b': b,
                               'low': low ,
                               'high': v})
                low=v
                v += step or 1
            data={'datafile': datafile,
                  'dbtype': dbtype,
                  'result_field': datafile.result_field,
                  'static': min_result == max_result,
                  'min': min_result,
                  'max': max_result,
                  'colors': colors,
                  'mapserver_template': settings.MAPSERVER_TEMPLATE }
            if dbtype == 'postgis':
                data['connectiontype']='POSTGIS'
                dbs=settings.DATABASES['default']
                data['connection']='''host={0} dbname={1} user={2} password={3} port={4}'''.format(dbs.get('HOST', None) or 'localhost',
                                                                                                   dbs.get('NAME'),
                                                                                                   dbs.get('USER'),
                                                                                                   dbs.get('PASSWORD'),
                                                                                                   dbs.get('PORT', None) or '5432')
                data['data']='nmtk_geometry from userdata_results_{0}'.format(datafile.pk)
                data['highlight_data']='''nmtk_geometry from (select * from userdata_results_{0} where nmtk_id in (%ids%)) as subquery
                                          using unique nmtk_id'''.format(datafile.pk)
            else:
                data['connectiontype']='OGR'
                data['connection']=datafile.sqlite_db.path
                data['data']='userdata_results_{0}'.format(datafile.pk)
                data['highlight_data']='''SELECT nmtk_geometry FROM "userdata_results_{0}" WHERE nmtk_id in (%ids%)'''.format(datafile.pk)
            res=render_to_string('NMTK_server/mapfile_{0}.map'.format(mapfile_type), 
                                 data)
            datafile.mapfile.save('mapfile.map', ContentFile(res), save=False)
            datafile.legendgraphic.save('legend.png', ContentFile(''), save=False)
            
            logger.debug('Creating a new legend graphic image %s', datafile.legendgraphic.path)
            im=generateColorRampLegendGraphic(min_text='{0}'.format(round(min_result,2)),
                                              max_text='{0}'.format(round(max_result,2)),
                                              units=datafile.result_field_units)
            im.save(datafile.legendgraphic.path, 'png')
            logger.debug('Image saved at %s', datafile.legendgraphic.path)
    except Exception, e:
        logger.exception ('Failed to create spatialite results table')
        return datafile
    logger.debug('About to return job back to caller - %s', datafile.pk)
    return datafile
    

@task(ignore_result=True)
def email_user_job_done(job):
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
    logger.debug('Sending job complete notification email to %s', job.user.email)
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
    if not toolserver.server_url.endswith('/'):
        append_slash='/'
    else:
        append_slash=''
    url="{0}{1}index".format(toolserver.server_url, append_slash) # index returns a json list of tools.
    tool_list=requests.get(url).json()
    logger.debug('Retrieved tool list of: %s', tool_list)
    for tool in tool_list:
        try:
            t=models.Tool.objects.get(tool_server=toolserver,
                                      tool_path=tool)
            # Clean up any sample files, we will reload them now.
            if hasattr(t,'toolsampleconfig'):
                t.toolsampleconfig.delete()    
            t.toolsamplefile_set.all().delete()
        except ObjectDoesNotExist:
            t=models.Tool(tool_server=toolserver,
                          name=tool)
        t.active=True
        t.tool_path=tool
        t.name=tool
        t.save()
    
    # Locate all the tools that aren't there anymore and disable them.
    for row in models.Tool.objects.exclude(tool_path__in=tool_list).filter(active=True, tool_server=toolserver):
        logger.debug('Disabling tool %s', row.name)
        row.active=False
        row.save()

@task(ignore_result=False)
def cancelJob(job_id, tool_id):
    '''
    Whenever a job that is active is cancelled, we need to notify the tool
    server to cancel the job as well.
    
    The tool doesn't support this (yet), since each tool might be different
    '''
    from NMTK_server import models
    logger=cancelJob.get_logger()
    tool=models.Tool.objects.get(pk=tool_id)
    logger.debug('Cancelling job %s to tool %s for processing', job_id,
                 tool)
    config_data=job_id
    digest_maker =hmac.new(str(job.tool.tool_server.auth_token), 
                           config_data, 
                           hashlib.sha1)
    digest=digest_maker.hexdigest()
    files={'cancel': ('cancel', job_id) }
    r=requests.delete(job.tool.analyze_url, files=files,
                    headers={'Authorization': digest })
    logger.debug("Submitted cancellation request for job to %s tool, response was %s (%s)", 
                 tool, r.text, r.status_code)
        
@task(ignore_result=False)
def submitJob(job_id):
    '''
    Whenever a job status is set to active in the database, the 
    signal attached to the model causes the job to be submitted.
    This causes this task (a celery task) to run, and submit
    the job to the tool.
    '''
    from NMTK_server import models
    job=models.Job.objects.get(pk=job_id)
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
    
    files= {'config': ('config', config_data) }
    for jobfile in job.jobfile_set.all():
        if jobfile.datafile.processed_file:
            files[jobfile.namespace]=(jobfile.datafile.processed_file.name, jobfile.datafile.processed_file)
        else:
            files[jobfile.namespace]=(jobfile.datafile.file.name, jobfile.datafile.file)
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
    if hasattr(tool, 'toolsampleconfig'):
        tool.toolsampleconfig.delete()
    tool.toolsamplefile_set.all().delete()
    try:
        logger.debug('Trying to load sample config for %s', tool.name)
        logger.debug('Config is %s', config_data)
        if (isinstance(config_data.get('sample', None), (dict,)) and 
            config_data['sample'].get('config')): 
            objects_to_save=[]
            objects_to_delete=[]
            tsc=models.ToolSampleConfig(sample_config=config_data['sample']['config'], 
                                        tool=tool)
            objects_to_save.append(tsc)
            reqd_fields=['namespace','checksum']
            for fconfig in config_data['sample'].get('files',[]):
                logger.debug('Working with %s', fconfig)
                sample_config_fields={'tool': tool}
                for f in reqd_fields:
                    if fconfig.has_key(f): 
                        sample_config_fields[f]=fconfig.get(f)
                    else:
                        raise Exception('Missing required field: %s' % (f,))
                m=models.ToolSampleFile(**sample_config_fields)
                if fconfig.has_key('uri'):
                    parsed=urlparse.urlparse(fconfig.get('uri'))
                    if not parsed.scheme:
                        if parsed.path[0] == '/':
                            p=urlparse.urlparse(tool.tool_server.server_url)
                            fconfig['uri']=urlparse.urlunparse([p.scheme,
                                                                p.netloc,
                                                                fconfig['uri'],
                                                                '',
                                                                '',
                                                                ''])
                        else:
                            raise Exception('Only absolute URLs or fully-qualified URLs allowed')
                    logger.debug('Attempting to download %s', fconfig['uri'])       
                    data=requests.get(fconfig['uri'], stream=True)
                    checksum=hashlib.sha1()
                    if data.status_code != 200:
                        raise Exception('Failed to download data file %s',
                                        fconfig['uri'])
                    logger.debug('Download succeeded!')
                    with tempfile.TemporaryFile() as f:
                        for chunk in data.iter_content(chunk_size=1024): 
                            if chunk: # filter out keep-alive new chunks
                                f.write(chunk)
                                checksum.update(chunk)
                                f.flush()
                        logger.debug('Checksum is %s=%s', fconfig['checksum'],
                                     checksum.hexdigest())
                        if checksum.hexdigest() == fconfig['checksum']:
                            f.seek(0)
                            # Get the file name
                            name=os.path.basename(urlparse.urlparse(fconfig['uri']).path)
                            if fconfig.has_key('content-type'):
                                m.content_type=fconfig['content-type']
                            elif data.headers.has_key('content-type'):
                                m.content_type=data.headers['content-type'].partition(';')[0]
                            else:
                                t=mimetypes.guess_type(fconfig['uri'])[0]
                                if t:
                                    m.content_type=t
                            m.file.save(name, File(f))
                            objects_to_delete.append(m)
            for m in objects_to_save:
                m2=models.ToolSampleConfig.objects.filter(tool=m.tool)
                if len(m2) == 1:
                    m.pk=m2[0].pk
            [m.save() for m in objects_to_save]
    except:
        logger.exception('Failed to load tool sample config.')
        # If we fail, we need to delete any downloaded files we saved.
        [m.delete() for m in objects_to_delete]

    # Note: We use update here instead of save, since we want to ensure that
    # we don't call the post_save handler, which would result in
    # a recursion loop.
    logger.debug('Setting tool name to %s', config_data['info']['name'])
    models.Tool.objects.filter(pk=config.tool.pk).update(name=config_data['info']['name'])
    
         
@task(ignore_result=False)
def importDataFile(datafile, job_id=None):
    from NMTK_server import models
    datafile.status_message=None
    try:
        loader=NMTKDataLoader(datafile.file.path, 
                              srid=datafile.srid)
        if loader.is_spatial:
            datafile.srid=loader.info.srid
            datafile.extent=geos.Polygon.from_bbox(loader.info.extent)
            datafile.srs=loader.info.srs
            datafile.geom_type=loader.info.type
        datafile.feature_count=loader.info.feature_count
        if loader.is_spatial and not datafile.srid:
            datafile.status=datafile.IMPORT_FAILED
            datafile.status_message='Please specify SRID for this file (unable to auto-identify SRID)'
        elif not job_id:
            datafile.status=datafile.IMPORTED
        else:
            datafile.status=datafile.IMPORT_RESULTS_COMPLETE
        datafile.fields=loader.info.fields
        # Create an empty file using ContentFile, then we can overwrite it 
        # with the desired GeoJSON data.
        if loader.is_spatial: 
            suffix='geojson'
        else: 
            suffix='json'
        if datafile.status in (datafile.IMPORTED, datafile.IMPORT_RESULTS_COMPLETE):
            datafile.processed_file.save('{0}.{1}'.format(datafile.pk, suffix), 
                                         ContentFile(''))
            loader.export_json(datafile.processed_file.path)
            generate_datamodel(datafile, loader)
        if job_id:
            try:
                job=models.Job.objects.get(pk=job_id)
                job.status=job.COMPLETE
            except: 
                logger.exception('Failed to update job status to complete?!!')
    except Exception, e:
        logger.exception('Failed import process!')
        datafile.processed_file=None
        if not job_id:
            datafile.status=datafile.IMPORT_FAILED
        else:
            datafile.status=datafile.IMPORT_RESULTS_FAILED
        datafile.status_message="%s" % (e,)
        if job_id:
            try:
                job=models.Job.objects.get(pk=job_id)
                job.status=job.POST_PROCESSING_FAILED
            except:
                logger.exception('Failed to update job status to failed?!!')
    if job_id:
        job.save()
    # Now we need to create the spatialite version of this thing.
    datafile.save()
    
    
