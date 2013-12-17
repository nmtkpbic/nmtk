from celery.task import task
import simplejson as json
import decimal
import requests
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

def generateColorRampLegendGraphic(min_text, max_text, height=16, width=258, border=1):
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
        text_height=max(min_text_height, max_text_height)+2
        final_width=max(width, max_text_width, min_text_width)
    else:
        max_text_width, max_text_height=font.getsize('All Features')
        text_height=max_text_height+2
        final_width=max(width, max_text_width)
    im2=Image.new('RGB', (final_width, height+text_height), "white")
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
def generate_sqlite_database(datafile, loader):
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
                database='%s'% (datafile.pk,)
                field_map=propertymap(row.keys())
                # Create the model for this data
                model_content.append('class Results(models.Model):')
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
                
                datafile.model.save('model.py', ContentFile('\n'.join(model_content)),
                                    save=False)
                #logger.debug('\n'.join(model_content))
                datafile.sqlite_db.save('db', ContentFile(''), save=False)
                settings.DATABASES[database]={'ENGINE': 'django.contrib.gis.db.backends.spatialite', 
                                              'NAME': datafile.sqlite_db.path }
                # Must stick .model in there 'cause django doesn't like models
                # without a package.
                user_model=imp.load_source('%s.models' % (datafile.pk,),datafile.model.path)
                connection=connections[database]
                connection.ops.spatial_version=(3,0,1)
                SpatiaLiteCreation(connection).load_spatialite_sql() 
                cursor=connection.cursor()
                for statement in connection.creation.sql_create_model(user_model.Results, no_style())[0]:
                    #logger.debug(statement)
                    cursor.execute(statement)
                for statement in connection.creation.sql_indexes_for_model(user_model.Results, no_style()):
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
                    min_result=min(float(this_row[datafile.result_field]), min_result)
                    max_result=max(float(this_row[datafile.result_field]), max_result)
                except Exception, e:
                    logger.debug('Result field is not a float (ignoring)')
            else:
                min_result=max_result=1
            m=user_model.Results(**this_row)
            m.save(using=database)
#             logger.debug('Saved model with pk of %s', m.pk)
        logger.debug('Completing transferring results to sqlite database %s', datafile.pk,)
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
            res=render_to_string('NMTK_server/mapfile_{0}.map'.format(mapfile_type), 
                                 {'datafile': datafile,
                                  'static': min_result == max_result,
                                  'min': min_result,
                                  'max': max_result,
                                  'colors': colors,
                                  'mapserver_template': settings.MAPSERVER_TEMPLATE })
            datafile.mapfile.save('mapfile.map', ContentFile(res), save=False)
            datafile.legendgraphic.save('legend.png', ContentFile(''), save=False)
            
            logger.debug('Creating a new legend graphic image %s', datafile.legendgraphic.path)
            im=generateColorRampLegendGraphic(min_text='{0}'.format(round(min_result,2)),
                                              max_text='{0}'.format(round(max_result,2)))
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
    for row in models.Tool.objects.exclude(tool_path__in=tool_list).filter(active=True, tool_server=toolserver):
        logger.debug('Disabling tool %s', row.name)
        row.active=False
        row.save()

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
        if not job_id:
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
        datafile.processed_file.save('{0}.{1}'.format(datafile.pk, suffix), 
                                     ContentFile(''))
        loader.export_json(datafile.processed_file.path)
        generate_sqlite_database(datafile, loader)
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
    
    
