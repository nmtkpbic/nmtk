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
from NMTK_apps.helpers.config_iterator import ConfigIterator

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
            file_iterator=ConfigIterator(input_files, file_namespace, setup)
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
            constant_iterator=ConfigIterator(input_files, 'coefficients', setup)
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
                             units='Average annual pedestrian count',
                             result_file='data',
                             files={'data': ('data.{0}'.format(file_iterator.extension),
                                             file_iterator.getDataFile(), 
                                             file_iterator.content_type)
                                    })
    for namespace, fileinfo in input_files.iteritems():
        os.unlink(fileinfo[0])

