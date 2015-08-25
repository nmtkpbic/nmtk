#
# 2013 - Chander Ganesan <chander@otg-nc.com>
# A Loader that understands the image formats that NMTK supports for in-browser
# data display.
#

import logging
import os
from mimetypes import MimeTypes
import cStringIO as StringIO
import magic
from BaseDataLoader import *
logger = logging.getLogger(__name__)


class ImageLoader(BaseDataLoader):
    name = 'image'

    def __init__(self, *args, **kwargs):
        '''
        Loading an image - hopefully
        '''
        logger.debug('ImageLoader: %s, %s', args, kwargs)
        self.filename = args[0][0]
        self.mimetype = magic.from_file(self.filename, mime=True)
        self.format = magic.from_file(self.filename)
        super(ImageLoader, self).__init__(*args, **kwargs)

    def __iter__(self):
        return self

    @property
    def extent(self):
        return None

    def next(self):
        '''
        Here we iterate over the results/values from this set of data.  If
        the data is spatial, we will return a tuple of the fields and the
        geometry data.  Otherwise a single value is returned that is
        a dictionary of the field data.
        '''
        raise StopIteration()

    @property
    def feature_count(self):
        '''
        Upon complete iteration through the data, we will have a feature count,
        so just loop through the data to count the features.
        '''
        return 0

    def fields(self):
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

    def is_supported(self):
        return (self.mimetype in ('image/png', 'image/jpeg', 'image/gif'))
