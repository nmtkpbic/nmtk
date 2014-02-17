from celery.task import task
import json
import datetime
from collections import namedtuple
import decimal
import math
import os
from django.core.serializers.json import DjangoJSONEncoder
import logging
logger=logging.getLogger(__name__)

def getPropertyMap( setup, elements, failures ):
    property_map={}
    for fieldspec in elements:
        if fieldspec['type'] == 'property':
            field = fieldspec['name']
            if setup.has_key(field):
                property_map[field] = setup[field]
            elif fieldspec.get('required',False):
                failures.append(("field '%s' (required) was not provided.") % (field,))
    return ( property_map, failures )

def getParameters( setup, elements, failures ):
    parameters={}
    for fieldspec in elements:
        field = fieldspec['name']
        parameters[field]=setup.get(field, fieldspec.get('default', None))
        if parameters[field] is None and fieldspec.get('required',False):
            failures.append("A value for field '%s' is required" % (field,))
    return ( parameters, failures )

class configIterator(object):
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
        

    

@task(ignore_result=False)
def performModel(input_files,
                 tool_config,
                 client,
                 perform_exp=False):
    '''
    This is where the majority of the work occurs related to this tool.
    The data_file is the input (probably spatial) data.
    The job_setup is a JSON object that contains the job configuration.
    The auth_key is the auth_key as passed by the NMTK server.  It needs
    to be used to pass things like status or results back to the NMTK server as 
    the job is processed.
    
    There's no model (yet) for this particular job - everything happens with the
    uploaded data file.  Later we can store/manage data for the job.
    
    The assumption here is that all relevant authorization/authentication has 
    happened prior to this job being run.
    '''
    logger=performModel.get_logger()
    logger.debug('Job input files are: %s', input_files)

    try:
        setup=json.loads(open(input_files['config'][0]).read()).get('analysis settings',{})
        # the name used for the File config object for this tool, so we can 
        # read the file from the config.
        file_namespace='data'
        failures=[]
        if (not isinstance(setup, (dict))):
            failures.append('Please provide analysis settings')
        else:
            logger.debug("Loaded config: %s", setup)
            file_iterator=configIterator(input_files, file_namespace, setup)
    except:
        logger.exception('Failed to parse config file or data file.')
        failures.append('Invalid job configuration')

    if failures:
        for f in failures:
            logger.debug("Failure: %s",f)
        client.updateResults(payload={'errors': failures },
                             failure=True)
    else:    
        client.updateStatus('Parameter & data file validation complete.')
        productSet=namedtuple('OLSSet', ['value','coefficient', 'parameter'])
        try:
            min = None
            max = None
            constant_iterator=configIterator(input_files, 'coefficients', setup)
            if constant_iterator.iterable:
                raise Exception('Constants cannot be iterable')
            else:
                constants=constant_iterator.data
            for row in file_iterator: # Loop over the rows in the input file
                # The "value" for the constants is 1, since nothing comes from
                # the file for this value.
                sets=[productSet(1,constants['constant'],'constant')]
                for field, value in row.iteritems():
                    constant_value=constants.get('{0}_coeff'.format(field), None)
                    if constant_value:
                        beta_set=productSet(value, 
                                            constant_value,
                                            field)
                        sets.append(beta_set)
                logger.debug('Sets currently %s', sets)
                result=sum([decimal.Decimal(str(s.value))*decimal.Decimal(str(s.coefficient)) 
                            for s in sets])
                result=result.exp()
                logger.debug("Data set is %s (Result: %s)", sets, result)
                result = float(result) # for correct JSON encoding
                file_iterator.addResult(setup['results']['result']['value'], result)    
        except Exception, e:
            # if anything goes wrong we'll send over a failure status.
            logger.exception('Job Failed with Exception!')
            client.updateResults(payload={'errors': [str(e),] },
                                 failure=True)
        # Since we are updating the data as we go along, we just need to return
        # the data with the new column (results) which contains the result of the 
        # model.
        client.updateResults(result_field=setup['results']['result']['value'],
                             result_file='data',
                             files={'data': ('data',file_iterator.getDataFile())
                                    })
    for namespace, fileinfo in input_files.iteritems():
        os.unlink(fileinfo[0])

