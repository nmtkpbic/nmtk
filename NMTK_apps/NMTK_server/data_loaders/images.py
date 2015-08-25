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
    supported_formats = ('image/png', 'image/jpeg', 'image/gif')

    def __init__(self, *args, **kwargs):
        '''
        Loading an image - hopefully
        '''
        self.unpack_list = []

        logger.debug('ImageLoader: %s, %s', args, kwargs)
        #
        # Iterate over the files that were passed in, and test each one
        # to see if they support the image format we allow, if they do, then
        # use the first one we find.
        #
        for filen in args[0]:
            mimetype = magic.from_file(filen, mime=True)
            if mimetype not in self.supported_formats:
                continue
            self.unpack_list.append(filen)
            self.filename = filen
            self.mimetype = mimetype
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
        return hasattr(self, 'mimetype') and (self.mimetype in self.supported_formats)
