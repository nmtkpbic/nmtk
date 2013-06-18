from celery.task import task
import json
import datetime
from collections import namedtuple
import decimal
import math
from django.core.serializers.json import DjangoJSONEncoder

@task(ignore_result=False)
def performModel(data_file, 
                 job_config, 
                 tool_config,
                 client,
                 perform_exp=False):
    '''
    This is where the majority of the work occurs related to this tool.
    The data_file is the input (probably spatial) data.
    The job_config is a JSON object that contains the job configuration.
    The auth_key is the auth_key as passed by the NMTK server.  It needs
    to be used to pass things like status or results back to the NMTK server as 
    the job is processed.
    
    There's no model (yet) for this particular job - everything happens with the
    uploaded data file.  Later we can store/manage data for the job.
    
    The assumption here is that all relevant authorization/authentication has 
    happened prior to this job being run.
    '''
    logger=performModel.get_logger()
    
    job_config=json.loads(open(job_config).read())['analysis settings']
    logger.debug(job_config)
    data_file=json.loads(open(data_file).read())
    tool_props=tool_config['input']['properties']
    property_map={}
    parameters={}
    failures=[]

    for field, fprops in tool_props.iteritems():
        if fprops['type'] == 'property':
            if job_config.has_key(field):
                property_map[field] = job_config[field]
            elif fprops.get('required',False):
                failures.append(('The field %s (required) was not ' + 
                                'provided.') % (field,))
        else: # These are the non-property types
            parameters[field]=job_config.get(field, 
                                             fprops.get('default', None))
            if parameters[field] is None and fprops.get('required',False):
                failures.append('A value for %s is required' % (field,))
    logger.debug('Parameters dictionary is %s', parameters)
    logger.debug('Mapping dictionary is %s', property_map)
    if failures:
        client.updateResults(data={'status': 'FAILED',
                                   'errors': failures})
    client.updateStatus('Parameter validation complete.')
    productSet=namedtuple('OLSSet', ['value','coefficient', 'parameter'])
    try:
        for row in data_file['features']:
            props=row['properties']
            sets=[productSet(job_config.get('constant', 
                                            tool_props['constant']['default']),
                             1,
                             'constant')]
            
            for key, source_field in property_map.iteritems():
                data_set=productSet(float(props[source_field]), 
                                    parameters.get('%s_coeff' % (key,), None),
                                    key)
                if data_set.coefficient:
                    sets.append(data_set)
            result=sum([decimal.Decimal(s.value)*decimal.Decimal(s.coefficient) 
                        for s in sets])
            if perform_exp: # The binomial model
                result=math.exp(result)
            logger.debug("Data set is %s (Result: %s)", sets, result) 
            props['result']=result
    except Exception, e:
        # if anything goes wrong we'll send over a failure status.
        logger.exception('Job Failed!')
        client.updateResults(data={'status': '%s' % (e,) }, 
                             failure=True)
    # Since we are updating the data as we go along, we just need to return
    # the data with the new column (results) which contains the result of the 
    # model.
    client.updateResults(json.dumps(data_file,
                                    cls=DjangoJSONEncoder))
    for f in [data_file, job_config]:
        os.path.unlink(f)