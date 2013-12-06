import logging
import collections
import os
from .BaseDataLoader import *

logger=logging.getLogger(__name__)


class BaseDataLoader(object):
    '''
    Base class for data loader.  Loaders should all support at the 
    very least the iterable protocol (returning a dictionary of key/value pairs)
    for each data set found.
    '''
    def __init__(self, filelist):
        '''
        A basic constructor to create a new data loader.  In this case
        the filelist is a list of prospective files to load - it generally
        comes from a zip (or some other) file type.
        '''
        self.filelist=filelist
        
    def is_supported(self):
        raise Exception('This method must be implemented')
    
    def __del__(self):
        if hasattr(self, 'temp_file'):
            os.unlink(self.temp_file)