import logging
import json
from django.core.serializers.json import DjangoJSONEncoder


logger=logging.getLogger(__name__)

class ConfigIterator(object):
    '''
    Returns an iterable object that returns rows of data, with each row
    of data being a dictionary whose keys are the names of the config fields.
    
    The idea here is that one of these is created for each of the namespaces
    and then used to retrieve values.  Ideally the tool will know when to use 
    these as an iterable vs as just getting a value set (obj.data) to work
    with.  
    
    Note: this used to use a namedtuple, but since it's possible that the
          "fields" could start with a number, this was changed to a dictionary.
    '''
    def __init__(self, input_files, namespace, config):
        logger.debug('Working with namespace %s', namespace)
        self.config_data=config[namespace]
        self.iterable_fields={}
        self._data={}
        for key, value in self.config_data.iteritems():
            if value['type'] == 'property':
                self.iterable_fields[key]=value['value']
            else:
                self._data[key]=value['value']
        logger.debug('Iterable fields are %s', self.iterable_fields)
        logger.debug('Constants are %s', self._data)
        logger.debug('Iterable is %s', self.iterable)
        if self.iterable:
            try:
                self.file_data=input_files[namespace][0] # The file name
            except:
                raise Exception(('Input file for namespace {0} is required, ' +
                                 'but not provided').format(namespace))
    @property
    def iterable(self):
        return len(self.iterable_fields) > 0
       
    @property
    def data(self):
        if not self.iterable:
            return self._data.copy()
        else:
            raise Exception('Iterable object cannot be used this way (check iterable attribute!)')
     
    def __iter__(self):
        self.stopIteration=False
        # assuming in this case that we have GeoJSON data, since that's what 
        # this particular tool requires.
        # if all the fields are static, then there's really no need to open the 
        # data file at all.
        if self.iterable:
            self.data_parsed=json.loads(open(self.file_data).read())
            self.file_iterator=iter(self.data_parsed['features'])
        return self
    
    def next(self):
        if self.stopIteration:
            raise StopIteration()
        if not self.iterable:
            self.stopIteration=True
            return self.data
        # Note: this will raise the stopiteration if there are no more rows
        # in the data file to work with.
        self.this_row=next(self.file_iterator)
        logger.debug('This row is %s', self.this_row)
        # Start with the static values, since those will always be the same
        data=self._data.copy()
        # copy in the non-static values (properties from the file)
        for k, v in self.iterable_fields.iteritems():
            data[k]=self.this_row['properties'][v]
        # return the data itself.
        logger.debug('Returning data of %s', data)
        return data
    
    def addResult(self, field, value):
        self.this_row['properties'][field]=value
        
    def getDataFile(self):
        return json.dumps(self.data_parsed, 
                          cls=DjangoJSONEncoder)
        
