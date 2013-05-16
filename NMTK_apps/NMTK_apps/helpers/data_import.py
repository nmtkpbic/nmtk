'''
This module is intended to provide components required to do the following:

- Create a Django model for a layer using ogrinspect
- Create a layermapping for loading data into the model
- Load a data file into the database using OGR
- It accepts (as input) an OGR supported data source and a table/model name.
  The table will be created and loaded with data, per the name specified.
  
Chander Ganesan, Open Technology Group, Inc <chander@otg-nc.com>
'''
import keyword
from django.contrib.gis.utils import mapping, ogrinspect, LayerMapping
from django.contrib.gis.utils.ogrinspect import _ogrinspect
from django.core.management.color import no_style
from NMTK_apps.helpers.srids import add_srs_entry
from django.db import connections
from django.contrib.gis.db.models.fields import GeometryField
from osgeo import ogr
import tempfile
import os
import shutil
import imp
import logging
from itertools import izip
import zipfile
import gzip
import tarfile
from django.contrib.gis.gdal.error import SRSException
log=logging.getLogger(__name__)
PG_SYSTEM_COLUMNS=['ctid','cmax','xmax','cmin','xmin','tableoid']
RESERVED_NAMES=PG_SYSTEM_COLUMNS + keyword.kwlist

SUPPORTED_EXTENSIONS=('.shp','.geojson','.kml','.vrt')
# A set of formats that we do not support via OGR (usually because they are potentially dangerous)
# The format should match the "Code" column of the formats supported list here: http://www.gdal.org/ogr/ogr_formats.html
# this is read-capable drivers only, since the write-only ones would be excluded by default.
EXCLUDED_FORMATS=('VRT',)

'''
from NMTK_apps.api_classes import data_import

f='/tmp/data.geojson'

o=data_import.DataLoader(f, 9999999)
'''

class UnCompressor(object):
    '''
    This class uncompresses .gz, tar.gz files, zip files, and zip files containing tar files.
    When it does so, it creates a flat directory structure and errors out if two file names collide within
    that structure.  It then returns a list of the fully qualified path to all the resulting files.
    '''
    clean=False
    def __init__(self, filename):
        self.dirname=tempfile.mkdtemp()
        self.filename=filename
    
    def cleanup(self):
        # ensure that multiple calls to this don't result in an exception
        if not self.clean:
            shutil.rmtree(self.dirname)
            self.clean=True
    
    def __del__(self):
        self.cleanup()
    
    def uncompress(self):        
        if self.filename.endswith('zip'):
            filenames=self.unzip(self.filename)
        elif self.filename.endswith('gz'):
            filenames=self.ungz(self.filename)
        else:
            filenames=[self.filename]
        reverse_enumerate = lambda l: izip(xrange(len(l)-1, -1, -1), reversed(l))
        for pos, filename in reverse_enumerate(filenames[:]):
            if tarfile.is_tarfile(filename):
                filenames[pos:pos+1]=self.untar(filename) # Replace the element with the stuff inside it
        return filenames
    
    def unzip(self, filename):
        filenames=[]
        zfile=zipfile.ZipFile(filename,'r')
        files=zfile.infolist()
        #
        # Regardless of the structure of the zipfile here, we'll always return a flattened structure (single directory of files.)
        # if a file appears twice, we'll just exit - that's not allowed!
        #
        for zinfoname in files:
            if zinfoname.filename.endswith('/'): continue
            filenames.append(os.path.basename(zinfoname.filename))
            if os.path.exists(os.path.join(self.dirname, filenames[-1])):
                raise Exception('Colliding file names (%s)' % (zinfoname.filename,))
            open(os.path.join(self.dirname, filenames[-1]),'wb').write(zfile.read(zinfoname.filename))
        return map(lambda f: os.path.join(self.dirname,f), filenames)
    
    def ungz(self, filename):
        f = gzip.open(filename, 'rb')
        filename=os.path.join(self.dirname,os.path.basename(filename[:-3]))
        open(filename,'w').write(f.read())
        return [filename]
    
    def untar(self, filename):
        filenames=[]
        tf=tarfile.open(filename)
        entry=tf.next()
        while entry is not None:
            if entry.isfile():
                filename=os.path.join(self.dirname, os.path.basename(entry.name))
                if os.path.exists(filename):
                    raise Exception('File name collission %s' % (filename,))
                open(filename,'wb').write(tf.extractfile(entry).read())
                filenames.append(filename)
            entry=tf.next()
        return filenames
        

class DataLoader(object):
    '''
    This class performs the tasks required to load a data file, it does the following:
        - Given a data file, it will create a model from the file.
        - The model will be instantiated into the database
        - The data from the file will be loaded into the database
    '''
    rows=0
    success=False
    addLayerResult=False
    def __init__(self, data_file, status_update_func=None, database='default', 
                 srid=None):
        self.messages=[]
        self.srid=srid
        self.database=database
        self.status_update_func=status_update_func
        self.connection=connections[database]
        self.data_file=data_file
        self.cursor=self.connection.cursor()
        self.summarize()
       
    def update_status(self, message):
        if self.status_update_func:
            self.status_update_func(message)
    
    def import_datafile(self, model_name):
        self.model_name=model_name
        if self.addLayer():
            self.instantiateModel()
            self.loadData()
            #self.addWebGeom()

    def str_to_module(self, module_name, data):
        module_file=tempfile.NamedTemporaryFile(dir='/dev/shm')
        module_file.write(data)
        module_file.flush()
        module=imp.load_source(module_name, module_file.name)
        return module
    
    def inspectData(self):
        '''
        "Enhance" ogrinspect that Django provides to support other non-shapefile data sources.  In this case,
        we're interested in GeoJSON, but it should be just as applicable for other source types as well.
        We'll also make this PostGIS specific and prohibit columns with PG-reserved names and Python 
        reserved keywords.
        '''
        self.detectSRID()
        self.field_swaps=[]
        model_gen=_ogrinspect(str(self.data_file), self.model_name, srid=self.geom_srid, 
                              geom_name='the_geom', decimal=True, blank=True, null=True, multi_geom=True)
        # Skip over the basic imports and comments, and class definition
        for row in model_gen:
            yield row
            if row.startswith('class'):
                yield "    # NMTK inserted primary key column"
                yield "    nmtk_feature_id=models.AutoField(primary_key=True)"
                break
        # check each row for collisions
        field_names=['objects']
        for row in model_gen:
            field_name, data_type=map(str.strip, row.strip().split('=',1))
            field_type, options=data_type.split('(',1)
            opts_dict={}
            options=options[:-1].strip()
            if options:
                for v in options.split(','):
                    key,value=map(str.strip,v.split('=',1))
                    opts_dict[key]=value
            if (field_type == 'models.CharField') and (opts_dict.get('max_length','1') == '0'):
                yield "    # Converted from %s to TextField, since length is indeterminate" % (field_type,)
                field_type='models.TextField'
                opts_dict['max_length']=65536
            new_field_name=field_name
            counter=1
            while new_field_name in field_names or new_field_name in RESERVED_NAMES:
                if field_type == 'models.GeoManager' and field_name == 'objects':
                    break
                new_field_name="%s_%d" % (field_name,counter)
                counter += 1
                
            if field_name != new_field_name:
                yield "    # Field name %s is a reserved name, or already used as a field" % (field_name,)
                if field_name not in PG_SYSTEM_COLUMNS and field_name not in field_names:
                    opts_dict['db_column']="'field_name'" # preserve the column name if possible.
                self.field_swaps.append((field_name, new_field_name))
                self.messages.append('Renamed field %s to %s (name conflicts with a reserved column, or another field)' % (field_name, new_field_name,))
                field_name=new_field_name
            field_names.append(field_name)
            yield "    %s = %s(%s)" % (field_name, field_type, ', '.join(["%s=%s" % (k,v) for k,v in opts_dict.iteritems()]))
                
        meta={'db_table': self.model_name,
              'app_label': 'NMTK_apps' }
        yield """\n    class Meta: """
        for k, v in meta.iteritems():
           yield "        %s='%s'" % (k, v)
           
    def generateMapping(self):
        layer_map=mapping(self.data_file, self.geom_field)
        swaps=dict(self.field_swaps)
        for key, value in layer_map.items():
            if swaps.has_key(key):
                del layer_map[key]
                layer_map[swaps[key]]=value
        return layer_map
    
    def detectSRID(self):
        '''
        Since Django doesn't always get us the SRID, we'll determine it ourself using OGR if possible.
        '''
        
        self.update_status('Determining summary information for data file (extents, SRID, geometry type, etc.)')
        ogr_obj=ogr.Open(self.data_file)
        if ogr_obj is None:
            raise Exception("Unable to determine file type")
        self.layer=ogr_obj.GetLayer()
        self.geom_extent=self.layer.GetExtent()
        self.geom_type=self.layer.GetGeomType()
        self.spatial_ref=self.layer.GetSpatialRef()
        self.spatial_ref.AutoIdentifyEPSG()
        self.geom_srid=self.spatial_ref.GetAuthorityCode(None)
        if self.geom_srid <= 0 or self.geom_srid is None:
            if self.srid:
                self.geom_srid=self.srid
            else:
                self.geom_srid=None
                return False
        else:
            return self.geom_srid
    
    def summarize(self):
        return self.detectSRID() # <-- Does most of the summary work!
        
    
    def addLayer(self):
        self.update_status('Introspecting format of datafile and generating data model')
        model_file=tempfile.NamedTemporaryFile(dir='/dev/shm')
        model_def='\n'.join(self.inspectData()) 
        #print model_def
        model_module=self.str_to_module(self.model_name, model_def)
        self.model=getattr(model_module,self.model_name)
        geom_field=None
        for field in self.model._meta.fields:
            if isinstance(field, GeometryField):
                self.geom_obj=field
                self.geom_field=field.name
                self.geom_type=field.geom_type
                break
        if self.geom_field is None:
            print "no geometry field found!"
            return False
        self.layer_map=self.generateMapping()
        model_file.close()
        self.addLayerResult=True
        return True
        
    def _executeSQL(self,statements):
        for statement in statements:
            log.debug(statement)
            self.cursor.execute(statement)
            
    def instantiateModel(self):
        self.update_status('Executing SQL to create database table for %s' % (self.model_name))
        style=no_style()
        for field in self.model._meta.fields:
            if isinstance(field, GeometryField):
                try:
                    add_srs_entry(field.srid, database=self.database)
                except SRSException, e:
                    log.error(e)
                    raise e
        self._executeSQL(self.connection.creation.sql_create_model(self.model, style)[0])
        self._executeSQL(self.connection.creation.sql_indexes_for_model(self.model, style))
        
    def loadData(self):
        self.update_status('Loading data into table %s' % (self.model_name))
        self.lm=LayerMapping(self.model, self.data_file, self.layer_map, transform=False)
        self.lm.save(stream=self, strict=True, verbose=False, progress=1)
        self.success=True
        
    def addWebGeom(self):
        self.update_status('Adding web geometry (EPSG 900913) data to %s' % (self.model_name))
        colname='web_geometry'
        statements=['''SELECT AddGeometryColumn('%s','%s',900913,'%s',2);''' % (self.model_name, colname,self.geom_type),
                    '''update %s set %s=st_transform(%s, 900913);''' % (self.model_name, colname, self.geom_field),
                    '''CREATE INDEX %s_%s_id on %s using GIST (%s);''' % (self.model_name, colname, self.model_name, colname),]
        self._executeSQL(statements)
        self.connection.commit()
    
    
    def updateLoadStatus(self, message):
        self.rows += 1 # update the number of rows loaded
        if self.rows % 100 == 0:
            self.update_status('Loaded %d rows of data into table %s (%s).' % (self.rows,self.model_name,message))
        log.debug(message)
    write=updateLoadStatus
    
    def __del__(self): # Ensure that we cleanup if we failed to complete the import.
        if self.success is False:
            self.resetDatabase()
    
    def resetDatabase(self):
        if hasattr(self,'model_name'):
            statements=['''drop table %s''' % (self.model_name,),]
            log.debug('Removing table %s', self.model_name)
            self._executeSQL(statements)
            GeometryColumns = self.connection.ops.geometry_columns()
            GeometryColumns.objects.filter(f_table_name=self.model_name).delete()
            self.connection.commit()
            
    



    