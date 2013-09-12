from celery.task import task
import json
import datetime
from collections import namedtuple
import decimal
import math
import os
from django.core.serializers.json import DjangoJSONEncoder

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

@task(ignore_result=False)
def performModel(data_file, 
                 job_setup, 
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

    setup=json.loads(open(job_setup).read()).get('analysis settings',{})
    failures=[]
    if (not isinstance(setup, (dict))):
        failures.append('Please provide analysis settings')
    else:
        logger.debug("Loaded config: %s", setup)
        source_data=json.loads(open(data_file).read())

        input = tool_config['input']
        for page in input:
            if 'type' in page and page['type']=='File':
                (property_map,failures) = getPropertyMap(setup, page['elements'],failures)
            else:
                (parameters,failures) = getParameters(setup, page['elements'],failures)

        logger.debug('Parameters dictionary is %s', parameters)
        logger.debug('Mapping dictionary is %s', property_map)

    if failures:
        for f in failures:
            logger.debug("Failure: %s",f)
        client.updateResults(data=json.dumps({'status': 'FAILED',
                                              'errors': failures},
                                            cls=DjangoJSONEncoder),
                             failure=True)
    else:    
        client.updateStatus('Parameter validation complete.')
        productSet=namedtuple('OLSSet', ['value','coefficient', 'parameter'])
        try:
            min = None
            max = None
            for row in source_data['features']:
                props=row['properties']
                sets=[productSet(1,parameters.get('constant',None),'constant')]
                for key, source_field in property_map.iteritems():
                    beta_set=productSet(float(props[source_field]), 
                                        parameters.get('%s_coeff' % (key,), None),
                                        key)
                    if beta_set.coefficient:
                        sets.append(beta_set)
                result=sum([decimal.Decimal(s.value)*decimal.Decimal(s.coefficient) 
                            for s in sets])
#                 if perform_exp: # The binomial model (not used in SF model)
#                     result=result.exp(result)
                #logger.debug("Data set is %s (Result: %s)", sets, result)
                result = float(result) # for correct JSON encoding
                props['result']=result
                min = result if not min or result < min else min
                max = result if not max or result > max else max
            source_data['range'] = [ min, max ]    
        except Exception, e:
            # if anything goes wrong we'll send over a failure status.
            logger.exception('Job Failed with Exception!')
            client.updateResults(json.dumps(data={'status': '%s' % (e,) },
                                            cls=DjangoJSONEncoder),
                                            failure=True)
        # Since we are updating the data as we go along, we just need to return
        # the data with the new column (results) which contains the result of the 
        # model.
        client.updateResults(data=json.dumps(source_data,
                                             cls=DjangoJSONEncoder))
    for f in [data_file, job_setup]:
        os.unlink(f)