from django.contrib.gis import models
from osgeo import ogr, osr
from setuptools import archive_util
import tempfile
import shutil
import os
import logging
import collections
logger=logging.getLogger(__name__)
from django.contrib.gis.geos import GEOSGeometry

class FormatException(Exception): 
    '''
    An exception raised when OGR was unable to determine the type of the
    input file (or files, in the case of an archive.) or there is some kind
    of format error - such as no provided SRID, too many layers, etc.
    '''
    pass


class DataLoader(object):
    def __init__(self, filename, content_type):
        self.content_type=content_type
        self.working_dir=tempfile.mkdtemp()
        self.filename=filename
        self.data=None
        
    def _get_filelist(self, filename):
        '''
        Unpack the archive if it is an archive, and return a list of 
        file names that should be examined by OGR to determine if they are
        OGR supported file types.
        
        Cache the result to speed up subsequent calls.
        '''
        if not hasattr(self, '_files', None):
            name, extension=os.path.splitext(filename)
            try:
                # Ensure that the files are output in the working dir, and 
                # subdirectories are omitted (so it's a flat dir structure)
                archive_util.unpack_archive(filename, self.working_dir,
                                            progress_filter=self._progress_filter)
                logger.debug('Unpacked archive %s to %s', filename, 
                             self.working_dir)
                files=[fn for fn in map(lambda dir: os.path.join(self.working_dir, 
                                                                 dir),
                                        os.listdir(self.working_dir)) 
                                        if not os.path.isdir(fn)]
            except archive_util.UnrecognizedFormat, e:
                logger.debug('Specified file (%s) is not a recognized archive',
                             filename)
                files=[filename,]
            self._files=files
        return self._files

class GeoDataLoader(DataLoader):
    '''
    The GeoDataLoader class accepts as input a single file and (optional) SRID
    information.  It then proceeds to parse and read from the file, using the
    OGR toolset.  If the file format is wrong, or something else bad happens
    then a FormatException is raised.  Once the GeoDataLoader object is created,
    it can then be used to retrieve the data back in the GeoJSON format, via the
    geojson attribute.
    '''
    types={ogr.wkbPoint: 'POINT',
           ogr.wkbGeometryCollection: 'GEOMETRYCOLLECTION',
           ogr.wkbLineString: 'LINESTRING',
           ogr.wkbMultiPoint: 'MULTIPOINT',
           ogr.wkbMultiPolygon: 'MULTIPOLYGON',
           ogr.wkbPolygon: 'POLYGON',
           ogr.wkbMultiLineString: 'MULTILINESTRING',}
    
    # if we get one of these types, we will convert them over to their 
    # mapped types
    type_conversions={ogr.wkbPoint: (ogr.wkbMultiPoint,ogr.ForceToMultiPoint),
                      ogr.wkbLineString: (ogr.wkbMultiLineString,ogr.ForceToMultiLineString),
                      ogr.wkbPolygon: (ogr.wkbMultiPolygon,ogr.ForceToMultiPolygon)}
    
    def __init__(self, *args, **kwargs):
        self.srid=kwargs.pop('srid',None)
        super(GeoDataLoader, self).__init__(*args, **kwargs)
        ogr_obj=self.geo_test(self.filename)
        ''' Test to see if we have OGR data, if so, load it - otherwise
            just process it like regular data.'''
        if ogr_obj:
            self.spatial=True
            self.process_data(self.filename, self.srid,
                              ogr_obj=ogr_obj)
            self.geojson_file=None
        else:
            self.spatial=False
            super(GeoDataLoader, self).process_data()
            
    def __del__(self):
        shutil.rmtree(self.working_dir,
                      ignore_errors=True)
    
    def _progress_filter(self, src, dest):
        return os.path.join(self.working_dir, os.path.basename(src))
        
    def geo_test(self, filename):
        '''
        A simple test of a file to see if it is geospatial in nature.
        '''
        files=self._get_filelist(self.filename)
        for fn in files:
            ogr_obj=ogr.Open(fn)
            if ogr_obj is not None:
                return ogr_obj
        if ogr_obj is None:
            return False
        
    def process_data(self, filename, srid=None, ogr_obj=None):
        '''
        The main processing function - here we will accept as input a file.
        If the file is an archive, we will unpack and get a list of its 
        composite files.  If it is not an archive, we will simply work with
        the single file provided to determine the type properly.
        
        Many sensible archive formats are supported, and any OGR supported
        file type works here.
        '''
        files=self._get_filelist(filename)
        layer=geom_extent=geom_type=spatial_ref=geom_srid=None
        if not ogr_obj:
            for fn in files:
                ogr_obj=ogr.Open(fn)
                if ogr_obj is not None:
                    break
            if ogr_obj is None:
                files_tried=','.join(map(os.path.basename, files))
                raise FormatException(('Unable to recognized the format,' +
                                       ' tried these files (%s) against' +
                                       ' %s different drivers') % 
                                       (files_tried, ogr.GetDriverCount()-1,))
        # If we get here, then we have successfully determined the file type
        # that was provided, using OGR.  ogr_obj contains the OGR DataSource
        # object, and fn contains the name of the file we read to get that.
        
        # We only support single layer uploads, if there is more than one
        # layer then we will raise an exception
        if ogr_obj.GetLayerCount() <> 1:
            raise FormatException('Too many (or too few) layers recognized ' +
                                  'in this data source (%s layers)',
                                  ogr_obj.GetLayerCount() )
        driver=ogr_obj.GetDriver()
        # Deny VRT files, since they can be used to reference any file on the
        # filesystem, and even external URLs.
        if 'vrt' in str(driver).lower():
            raise FormatException('VRT format datafiles are not currently ' +
                                  'supported')
        
        layer=ogr_obj.GetLayer()
        geom_extent=layer.GetExtent()
        geom_type=layer.GetGeomType()
        if geom_type not in self.types:
            raise FormatException('Unsupported Geometry Type (%s)' % (geom_type,))
        spatial_ref=layer.GetSpatialRef()
        if spatial_ref and not srid:
            spatial_ref.AutoIdentifyEPSG()
            geom_srid=srid or spatial_ref.GetAuthorityCode(None)
        elif srid:
            geom_srid=srid
            srs=osr.SpatialReference()
            epsg=str('EPSG:%s' % (geom_srid,))
            logger.debug('Setting output SRID to %s (%s)', 
                         epsg, type(epsg))
            srs.SetFromUserInput(epsg)
        if (geom_srid <= 0 or geom_srid is None) and not spatial_ref:
            raise FormatException('Unable to determine valid SRID ' + 
                                  'for this data')
            
        # Get fields by looping over one row of features.
        fields=[]
        for feat in layer:
            for i in range(feat.GetFieldCount()):
                field_definition=feat.GetFieldDefnRef(i)
                fields.append(field_definition.GetNameRef ())
            break
#         logger.debug('Fields are %s', fields)
        # Just to be on the safe side..
        layer.ResetReading()
        
        OGRResult=collections.namedtuple('OGRResult',
                                         ['srid',
                                          'extent',
                                          'srs',
                                          'layer',
                                          'feature_count',
                                          'ogr',
                                          'type',
                                          'type_text',
                                          'fields','reprojection', 
                                          'dest_srs'])
        # Note that we must preserve the OGR object here (even though
        # we do not use it elsewhere), because
        # otherwise it gets garbage collected, and the OGR Layer object
        # will break.
        if geom_type in self.type_conversions:
            logger.debug('Converting geometry from %s to %s (geom_type upgrade)',
                         geom_type, self.type_conversions[geom_type][0])
            geom_type, self._geomTransform=self.type_conversions[geom_type]
        else:
            self._geomTransform=lambda a: a
        
        epsg_4326=osr.SpatialReference()
        epsg_4326.SetWellKnownGeogCS("EPSG:4326")
        if (not spatial_ref.IsSame(epsg_4326)):
            reprojection=osr.CoordinateTransformation( spatial_ref, epsg_4326 )
        else:
            reprojection=None
        self.data=OGRResult(srid=geom_srid,
                            extent=geom_extent,
                            ogr=ogr_obj,
                            layer=layer,
                            srs=spatial_ref,
                            feature_count=layer.GetFeatureCount(),
                            type=geom_type,
                            type_text=self.types[geom_type],
                            fields=fields,
                            dest_srs=epsg_4326,
                            reprojection=reprojection)
        return self.data
    
    def geomTransform(self, feature):
        if feature:
            transform=getattr(self, '_geomTransform', None)
            if transform or self.data.reprojection:
                geom=feature.geometry()
                if transform:
                    geom=transform(geom)
                if self.data.reprojection:
                    geom.Transform( self.data.reprojection )
                # in theory this makes a copy of the geometry, which
                # feature then copies - but it seems to fix the crashing issue.
                feature.SetGeometry(geom.Clone())
        return feature 
    
    @property
    def info(self):
        '''
        Returns an OGRResult object which contains all the information that 
        we were able to determine about this particular datafile.
        '''
        return self.data
    
    def __iter__(self):
        self.data.layer.ResetReading()
        return self
    
    def next(self):
        feature=self.data.layer.GetNextFeature()
        if not feature:
            raise StopIteration
        else:
            feature=self.geomTransform(feature)
            data=dict((field, getattr(feature, field)) for field in self.data.fields)
            logger.debug('Returning data for next feature...')
            d= (data, feature.geometry().ExportToWkt())
            logger.debug('Converted data to WKT (%s)', d[1])
            return d
    
    @property
    def geojson(self):
        if self.geojson_file:
            return self.geojson_file
        if not self.data:
            raise Exception('Unable to generate a GeoJSON file without ' +
                            'having already processed an input file.')
        # Get the GeoJSON driver
        driver = ogr.GetDriverByName('GeoJSON')
        # Get a file for the data source:
        tempfn=tempfile.NamedTemporaryFile(suffix='.geojson',
                                           dir=self.working_dir).name
#         srs=osr.SpatialReference()
#         srs.SetFromUserInput('EPSG:%s' % (self.data.srid,))
        # Cannot use the method below, since we need to ensure that
        # the CRS Information is properly set in the GeoJSON output.
#        datasource=driver.CopyDataSource(self.data.ogr, tempfn,
#                                         options=('a_srs', self.data.srid))
        datasource = driver.CreateDataSource(tempfn)
        
        
        layer=datasource.CreateLayer('GeoJSON',
                                     geom_type=self.data.type,
                                     srs=self.data.dest_srs)
        self.data.layer.ResetReading()
        while True:
            feature=self.data.layer.GetNextFeature()
            if not feature: break
            feature=self.geomTransform(feature)
            logger.debug('Creating next feature in output dataset')
            layer.CreateFeature(feature)
        
        layer.SyncToDisk()
        datasource.SyncToDisk()
        logger.error('Saved data to disk (sync) and remove objects!')
        self.geojson_file=tempfn
        return tempfn