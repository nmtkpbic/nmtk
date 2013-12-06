#
# 2013 - Chander Ganesan <chander@otg-nc.com>
# A Loader that creates an iterable object from many tabular data formats
# including dbf, xls, csv, etc. and supports a wide range of different
# delimeters.  Additionally, if geo-fields are recognized, returns a 
# geometry result that includes the geo-data fields as appropriate.
#

from osgeo import ogr, osr
import logging
import collections
import tempfile
import os
import csvkit
from csvkit import convert # guess_format
import decimal
import csv
from mimetypes import MimeTypes
import cStringIO as StringIO
from django.contrib.gis.geos import GEOSGeometry
from BaseDataLoader import *

logger=logging.getLogger(__name__)

class CSVLoader(BaseDataLoader):
    name='csv'
    def __init__(self, *args, **kwargs):
        '''
        Note if fieldnames is passed in it is assumed to be a list of field
        names for this file (normally would be the header line of the CSV - 
        first line of data.)  If skip_header is passed in, the assumption is 
        that the first line of the file should be skipped.  Note that the default
        is to use the first line for the header, so the setting only makes sense
        when fieldnames is passed in.
        
        Note that if this module is used to produce spatial data, the SRID of
        the data is ALWAYS EPSG:4326, this format only supports that single 
        projection type.
        '''
        logger.debug('CSVLoader: %s, %s', args, kwargs)
        self.fieldnames=kwargs.pop('fieldnames', None)
        # Passed in if we provide fieldnames and a header is present.
        self.skip_header=kwargs.pop('skip_header', False)
        if not self.fieldnames:
            self.skip_header=False
        super(CSVLoader, self).__init__(*args, **kwargs)
        self.process_file()
    
    def __iter__(self):
        if not hasattr(self ,'_feature_count'):
            self.feature_counter=0
        if self.filename:
            self.csv=csvkit.CSVKitDictReader(open(self.filename,'r'), 
                                             self.fieldnames,
                                             dialect=self.dialect)
            if self.skip_header:
                self.csv.next()   
        return self   
            
    def is_valid_range(self, v, max):
        '''
        Used for determining if a lat or long passed in via a delimited
        file is a valid set of values or not.  Our test in this case
        is to see if it is between the range +/-90 for lat and
        +/-180 for lat (the caller passes in the range as the max argument.)
        '''
        try:
            v=decimal.Decimal(v)
        except:
            return None
        if abs(v) <= max:
            return v
        return None


    @property
    def extent(self):
        if self.spatial:
            if not hasattr(self, '_extent'):
                for v in self: pass
            return self._extent
            

    def next(self):
        '''
        Here we iterate over the results/values from this set of data.  If
        the data is spatial, we will return a tuple of the fields and the
        geometry data.  Otherwise a single value is returned that is 
        a dictionary of the field data.
        '''
        try:
            data=self.csv.next()
            if not hasattr(self ,'_feature_count'):
                self.feature_counter += 1
        except StopIteration, e:
            self._feature_count=self.feature_counter
            if hasattr(self, '_union_geom'):
                self._extent=self._union_geom.extent
            raise StopIteration
        if getattr(self, 'spatial', False):
            lat=self.is_valid_range(data.get(self.latitude_field, None),
                                    90)
            lon=self.is_valid_range(data.get(self.longitude_field, None),
                                    180)
            if lat and lon:
                wkt='POINT({0} {1})'.format(lat,
                                            lon,)
                if not hasattr(self, '_extent'):
                    if not hasattr(self, '_union_geom'):
                        self._union_geom=GEOSGeometry(wkt)
                    else:
                        self._union_geom=self._union_geom.union(GEOSGeometry(wkt))
            else:
                wkt=None
            return (data, wkt)
        return (data, None)
    
    @property
    def feature_count(self):
        '''
        Upon complete iteration through the data, we will have a feature count,
        so just loop through the data to count the features.
        '''
        if not hasattr(self, '_feature_count'):
            for v in self: pass
        return self._feature_count
    
    def process_file(self):
        '''
        Here we will see if the input file is CSV, or if it is an understood
        format that can be converted to CSV.  Assuming it's one of those two,
        we will pass the resulting CSV file over to the csv processor.
        '''
        for this_filename in self.filelist:
            logger.debug('Filename processing is %s', this_filename)
            self.format=convert.guess_format(this_filename)
            logger.debug('Guessed format of %s', self.format)
            if self.format == 'csv':
                self.filename=this_filename
                break
            elif self.format:
                # If it is not a CSV file, but some other
                # understood format, we will convert it to a CSV and
                # write it out to a temporary file.
                fh, self.temp_file=tempfile.mkstemp(suffix='.csv')
                self.filename=self.temp_file
                try:
                    logger.debug('Attempting to convert to format CSV (from %s)',
                                 self.format)
                    with open(self.temp_file,'w') as fh:
                        fh.write(convert.convert(open(this_filename,'rb'), 
                                                 self.format))
                    break
                except Exception, e:
                    logger.exception('Failed to process %s to CSV: %s',
                                     self.filename, e)
                    os.unlink(self.filename)
                    self.filename=None
                
        if getattr(self, 'filename', None):
            return self.process_csv(self.filename)

    def fields(self):
        return self._fields

    def process_csv(self, filename):
        '''
        Here we have a CSV file that we need to process...
        '''
        try:
            data=open(filename,'r').read(1024)
            logger.debug('Data is %s', data)
            self.dialect=csvkit.sniffer.sniff_dialect(data)
            logger.debug('Dialect is %s', self.dialect)
            if self.dialect:
                self.filename=filename
            else:
                logger.warn('Unable to determine dialect in use for CSV file (%s)',
                            filename)
        except Exception as e:
            logger.warn('Found a CSV file (%s) with an invalid format: %s',
                        filename, e)     
        if self.filename:
            reader=csvkit.CSVKitDictReader(open(self.filename, 'r'),
                                           self.fieldnames,
                                           dialect=self.dialect)
            if self.skip_header:
                reader.next()
            self._fields=reader.fieldnames
            latitude_field_candidates=['latitude','lat']
            longitude_field_candidates=['longitude','long', 'lon']
            lat=long=False
            # case-insensitive check to see if lat/long is in the resulting
            # fields from the data
            for field in latitude_field_candidates:
                for this_field in self._fields:
                    if field == this_field.lower():
                        lat=this_field
                        break
            for field in longitude_field_candidates:
                for this_field in self._fields:
                    if field == this_field.lower():
                        long=this_field
                        break
            if lat and long:
                # Here it is assumed we have geo-data, so we will
                # convert it to a GIS format and then handle it as such
                # going forward.
#                 self._fields.remove(lat)
#                 self._fields.remove(long)
                self.latitude_field=lat
                self.longitude_field=long
                self.spatial=True
                self.spatial_type=ogr.wkbPoint
                self.srid=4326
                srs=osr.SpatialReference()
                epsg=str('EPSG:%s' % (self.srid,))
                srs.SetFromUserInput(epsg)
                self.srs=srs.ExportToWkt()
                
            
    def is_supported(self):
        if getattr(self, 'filename', None):
            return True
        else:
            return False