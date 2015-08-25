import logging
import collections
import datetime
from dateutil.parser import parse
from BaseDataLoader import *
from loaders import FormatException
from ogr import osr
from django.contrib.gis.gdal import \
    GDALRaster, SpatialReference, CoordTransform
from django.contrib.gis.geos import Polygon

logger = logging.getLogger(__name__)


class RasterLoader(BaseDataLoader):
    name = 'Raster'

    types = 99

    def __init__(self, *args, **kwargs):
        '''
        A reader for GDAL support raster images.
        '''
        self.raster_obj = None
        self._srid = kwargs.pop('srid', None)
        super(RasterLoader, self).__init__(*args, **kwargs)
        for fn in self.filelist:
            try:
                self.raster_obj = GDALRaster(fn)
            except:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.exception('Failed to open file %s', fn)
                else:
                    logger.info('The GDAL Loader does not support this data ' +
                                'format, deferring to the next loader ' +
                                'in the chain.')
                self.ogr_obj = None
            if self.raster_obj is not None:
                self.spatial = True
                self.format = self.raster_obj.driver.name
                logger.debug('The format of the file is %s', self.format)
                self.filename = fn
                break

    @property
    def dimensions(self):
        return 2

    def determineGeometryType(self, layer):
        '''
        In the case of a KML/KMZ file, we need to iterate over the data to determine
        the appropriate geometry type to use.
        '''
        return None

    def __iter__(self):
        return iter([])

    @property
    def spatial_type(self):
        return self.data.type

    @property
    def feature_count(self):
        return self.data.feature_count

    @property
    def srs(self):
        return self.data.srs

    @property
    def srid(self):
        return self.data.srid

    def is_supported(self):
        '''
        Indicate whether or not this loader is able to process this
        file type.  If it is, return True, otherwise return False.

        In this case, we return true if it's an OGR supported file type.
        '''
        if self.raster_obj:
            return True
        return False

    def fields(self):
        '''
        This was changed so now our field list is actually a list of fields
        and their respective data types.  So now we need to preserve the support
        of retrieval of fields for backwards compatibility.
        '''
        return []

    def fields_types(self):
        '''
        This returns a list of tuples, with the first being a field name
        and the second element of each being the python type of the field.
        '''
        return []

    def ogr_fields_types(self):
        '''
        This returns a list of tuples, with the first being a field name
        and the second element of each being the python type of the field.
        '''
        return []

    @property
    def extent(self):
        return (self.data.extent[0], self.data.extent[2],
                self.data.extent[1], self.data.extent[3],)

    @property
    def data(self):
        '''
        Read the output file and provide an iterable result
        '''
        if not hasattr(self, '_data'):
            if self.raster_obj is None:
                self._data = None
                return None
            layer = geom_extent = geom_type = spatial_ref = geom_srid = None
            # If we get here, then we have successfully determined the file type
            # that was provided, using OGR.  ogr_obj contains the OGR DataSource
            # object, and fn contains the name of the file we read to get that.

            # We only support single layer uploads, if there is more than one
            # layer then we will raise an exception
            driver = self.raster_obj.driver.name

            layer = None
            geom_extent = self.raster_obj.extent
            geom_type = 99

            srs = self.raster_obj.srs
            geos_extent = Polygon.from_bbox(self.raster_obj.extent)
            ogr_extent = geos_extent.ogr
            srid = None
            # USer supplied SRID, so we will use that...
            if self._srid:
                srs = None
                geom_srid = self._srid
                epsg = str('EPSG:%s' % (geom_srid,))
                logger.debug('Setting output SRID to %s',
                             epsg)
                try:
                    srs = SpatialReference(epsg)

                    srs.validate()
                    geom_srid = srs.srid
                except Exception, e:
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.exception('Invalid SRS (or none): %s', e)
                    srs = None
            # No SRID! Let's try to detect it
            if srs and not geom_srid:
                srs.identify_epsg()
                geom_srid = srs.srid
                logger.debug('Auto-detect of SRID yielded %s', srid)
            if srs and not geom_srid:
                '''
                Still no SRID - but we have an srs - so let's try to 
                reproject...
                '''
                try:
                    reprojection = CoordTransform(
                        r.srs, SpatialReference('EPSG:4326'))
                    ogr_extent.transform(reprojection)
                    geos_extent = ogr_extent.geos
                    geom_srid = geos_extent.srid
                except Exception, e:
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.exception('Failed to transform: %s', e)
                    raise FormatException('Unable to determine valid SRID ' +
                                          'for this data')
            if not geom_srid:
                raise FormatException('Unable to determine valid SRID ' +
                                      'for this data')

            # Ensure we have an extent that is in EPSG 4326
            if geom_srid != 4326:
                reprojection = CoordTransform(
                    srs, SpatialReference('EPSG:4326'))
                ogr_extent.transform(reprojection)
                geos_4326 = ogr_extent.geos
                geom_srid = 4326
            else:
                geos_4326 = geos_extent

            RasterResult = collections.namedtuple('RasterResult',
                                                  ['srid',
                                                   'extent',
                                                   'srs',
                                                   'layer',
                                                   'feature_count',
                                                   'ogr',
                                                   'type',
                                                   'type_text',
                                                   'fields',
                                                   'reprojection',
                                                   'dest_srs',
                                                   'dim', ])

            self._data = RasterResult(srid=geom_srid,
                                      extent=geos_4326.extent,
                                      ogr=None,
                                      layer=None,
                                      srs=geos_4326.srs,
                                      feature_count=0,
                                      type=geom_type,
                                      type_text='Raster',
                                      fields=[],
                                      dest_srs=None,
                                      reprojection=None,
                                      dim=self.dimensions)
        return self._data
