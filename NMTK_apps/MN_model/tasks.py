from celery.task import task
import json
import datetime
from collections import namedtuple
import decimal
import math
import os
from django.core.serializers.json import DjangoJSONEncoder
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
                if perform_exp: # The binomial model
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


# @task(ignore_result=False)
# def performModel(input_files,
#                  tool_config,
#                  client,
#                  perform_exp=False):
#     '''
#     This is where the majority of the work occurs related to this tool.
#     The data_file is the input (probably spatial) data.
#     The job_setup is a JSON object that contains the job configuration.
#     The auth_key is the auth_key as passed by the NMTK server.  It needs
#     to be used to pass things like status or results back to the NMTK server as 
#     the job is processed.
#     
#     There's no model (yet) for this particular job - everything happens with the
#     uploaded data file.  Later we can store/manage data for the job.
#     
#     The assumption here is that all relevant authorization/authentication has 
#     happened prior to this job being run.
#     '''
#     logger=performModel.get_logger()
# 
#     setup=json.load(open(job_setup)).get('analysis settings',{})
#     failures=[]
#     if (not isinstance(setup, (dict))):
#         failures.append('Please provide analysis settings')
#     else:
#         logger.debug("Loaded config: %s", setup)
#         source_data=json.loads(open(data_file).read())
# 
#         input = tool_config['input']
#         for page in input:
#             if 'type' in page and page['type']=='File':
#                 (property_map,failures) = getPropertyMap(setup, page['elements'],failures)
#             else:
#                 (parameters,failures) = getParameters(setup, page['elements'],failures)
# 
#         logger.debug('Parameters dictionary is %s', parameters)
#         logger.debug('Mapping dictionary is %s', property_map)
# 
#     if failures:
#         for f in failures:
#             logger.debug("Failure: %s",f)
#         client.updateResults(payload={'errors': failures },
#                              failure=True)
#     else:    
#         client.updateStatus('Parameter validation complete.')
#         productSet=namedtuple('OLSSet', ['value','coefficient', 'parameter'])
#         try:
#             min = None
#             max = None
#             for row in source_data['features']:
#                 props=row['properties']
#                 sets=[productSet(1,parameters.get('constant',None),'constant')]
#                 for key, source_field in property_map.iteritems():
#                     beta_set=productSet(float(props[source_field]), 
#                                         parameters.get('%s_coeff' % (key,), None),
#                                         key)
#                     if beta_set.coefficient:
#                         sets.append(beta_set)
#                 result=sum([decimal.Decimal(s.value)*decimal.Decimal(s.coefficient) 
#                             for s in sets])
#                 if perform_exp: # The binomial model
#                     result=result.exp()
#                 #logger.debug("Data set is %s (Result: %s)", sets, result)
#                 result = float(result) # for easy JSON encoding
#                 props['result']=result
#                 min = result if not min or result < min else min
#                 max = result if not max or result > max else max
#             source_data['range'] = [ min, max ]    
#         except Exception, e:
#             # if anything goes wrong we'll send over a failure status.
#             logger.exception('Job Failed with Exception!')
#             client.updateResults(json.dumps(data={'status': '%s' % (e,) },
#                                             cls=DjangoJSONEncoder),
#                                             failure=True)
#         # Since we are updating the data as we go along, we just need to return
#         # the data with the new column (results) which contains the result of the 
#         # model.
#         client.updateResults(result_field='result',
#                              result_file='data',
#                              files={'data': ('data',json.dumps(source_data,
#                                                                cls=DjangoJSONEncoder))
#                                     })
#     for f in [data_file, job_setup]:
#         os.unlink(f)
