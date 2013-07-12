from tests.utils.NMTKTestCase import NMTKTestCase
from tests.utils.client import NMTKClient
import logging
import simplejson as json
import os
import time
from mechanize import ParseFile
import StringIO
logger=logging.getLogger(__name__)

class TestJobConfiguration(NMTKTestCase):
    
    def setUp(self):
        super(TestJobConfiguration, self).setUp()
        
    def tearDown(self):
        super(TestJobConfiguration, self).tearDown()
        
    def test_setup_job(self):
        '''
        Upload and supply a data file for some jobs, then verify the form comes back.
        '''
        username, password=self.getUsernamePassword()
        user_uri=self._create_user(username,password)
        client=NMTKClient(self.site_url)
        response=client.login(username=username,
                              password=password)
        filename=self.get_support_file('test1.geojson')
        test_file=client.uploadData(filename, 
                                    description='Test data file (MSP)')
        logger.debug('URI of test file is %s', test_file)
        
        tool_url=client.getURL('api','tool/')
        job_url=client.getURL('api','job/')
        response=client.get(tool_url, params={'format': 'json'})
        tools=response.json()['objects']
        tool_uri_list=[]
        # Get a list of all the Tool Resource URIs for Minnesota models,
        # since the test1.geojson file is a MN model-specific data file.
        for tool in tools:
            if 'minnesota' in tool['name'].lower():
                tool_uri_list.append(tool['resource_uri'])
        job_uri_list=[]
        for uri in tool_uri_list:
            data={'tool': client.neuter_url(uri),
                  'data_file': client.neuter_url(test_file)}
            response=client.post(job_url, 
                                 data=json.dumps(data),
                                 headers={'Content-Type': 'application/json',})
            self.assertEqual(response.status_code, 201,
                             ('Expected job to be created - ' +
                              'got back %s instead') % (
                             response.status_code))
            logger.debug('Created new job entry with URI %s', 
                         response.headers['location'])
            job_uri_list.append(response.headers['location'])
        for uri in job_uri_list:
            response=client.get(uri, params={'format': 'json'})
            data=response.json()
            self.assertTrue(len(json.dumps(data.get('form',''))) > 10, 
                            'Expected the form to appear in' +
                            'the output JSON (got %s)' % (response.text,))
            
    def test_submit_job(self):
        '''
        Verify that we can properly submit a job (form) via the API and \
get back the (eventual) results and status of the running job.
        '''
        username, password=self.getUsernamePassword()
        user_uri=self._create_user(username,password)
        client=NMTKClient(self.site_url)
        response=client.login(username=username,
                              password=password)
        filename=self.get_support_file('test1.geojson')
        test_file=client.uploadData(filename, 
                                    description='Test data file (MSP)')
        logger.debug('URI of test file is %s', test_file)
        
        tool_url=client.getURL('api','tool/')
        job_url=client.getURL('api','job/')
        response=client.get(tool_url, params={'format': 'json'})
        tools=response.json()['objects']
        # Get a list of all the Tool Resource URIs for Minnesota models,
        # since the test1.geojson file is a MN model-specific data file.
        for tool in tools:
            if 'minnesota' in tool['name'].lower():
                tool_uri=tool['resource_uri']
                break
        data={'tool': client.neuter_url(tool_uri),
              'data_file': client.neuter_url(test_file)}
        
        response=client.post(job_url, 
                             data=json.dumps(data),
                             headers={'Content-Type': 'application/json',})
        logger.debug('Result from post was %s', response.text)
        self.assertEqual(response.status_code, 201,
                         ('Expected job to be created - ' +
                          'got back %s instead') % (response.status_code,))
        job_uri=response.headers['location']
        # Now we have a job, let's get the form, generate the response, and
        # submit it back to the user.
        response=client.get(job_uri, params={'format': 'json'}).json()
#        logger.debug(response['form']['fields'])
        
        form = '<form method="POST" action="%s/configure/">' % (job_uri,)
        form +='\n'.join([field['field'] for field_name, field in 
                        response['form']['fields'].iteritems()])
        form += '</form>'
#        logger.debug('Parsed form as %s', form)
        
        mform=ParseFile(StringIO.StringIO(form), job_uri,
                        backwards_compat=False)
        logger.debug('Parsed form was %s', mform[0])

        post_dict=dict([(f.name, f.value) for f in mform[0].controls])
        for k, v in post_dict.iteritems():
            if isinstance(v, (list, tuple)) and len(v) == 1:
                post_dict[k]=v[0]
        logger.debug('Form parsed is %s', post_dict)
        response['config']=post_dict
        
        response=client.put(job_uri, headers={'Content-Type': 'application/json',},
                            data=json.dumps(response))
        logger.debug('Response from job update was %s', response.text)
        self.assertEqual(response.status_code, 204,
                         'Expected a return code of 204 with valid data provided')
        
        
        self.fail('INCOMPLETE TEST')
            
        
        
    
    def test_prevent_user_from_using_other_user_data(self):
        '''
        Verify that one user can neither access, nor submit jobs, with another users data
        '''
        username, password=self.getUsernamePassword()
        user_uri=self._create_user(username,password)
        username2, password2=self.getUsernamePassword()
        user_uri=self._create_user(username2,password2)
        client=NMTKClient(self.site_url)
        client.login(username=username,
                     password=password)
        client2=NMTKClient(self.site_url)
        client2.login(username=username2,
                      password=password2)
        filename=self.get_support_file('test1.geojson')
        test_file=client.uploadData(filename, 
                                    description='Test configuration file')
        # Just try to access the other users file
        response=client2.get(test_file, params={'format': 'json'})
        logger.debug('Response when getting other users file was %s',
                     response.status_code)
        self.assertEqual(response.status_code, 401,
                         'Expected a 401, got a %s' % (response.status_code,))
        # Try to create a job with the other users file
        job_url=client.getURL('api','job/')
        tool_url=client.getURL('api','tool/')

        response=client.get(tool_url, params={'format': 'json'})
        tools=response.json()['objects']
        # Get a list of all the Tool Resource URIs for Minnesota models,
        # since the test1.geojson file is a MN model-specific data file.
        for tool in tools:
            if 'minnesota' in tool['name'].lower():
                tool_uri=tool['resource_uri']
                break
        data={'tool': client.neuter_url(tool_uri),
              'data_file': client.neuter_url(test_file)}
        logger.debug('Verifying that user A cannot create a job with User B data')
        response=client2.post(job_url, 
                              data=json.dumps(data),
                              headers={'Content-Type': 'application/json',})
        logger.debug('Status code was %s', response.status_code)
        logger.debug('Response text was %s', response.text)

    def test_submit_job_other_user_denied_access(self):
        '''
        Verify that once a job is submitted/created, other users cannot access.
        '''
        username, password=self.getUsernamePassword()
        user_uri=self._create_user(username,password)
        client=NMTKClient(self.site_url)
        response=client.login(username=username,
                              password=password)
        username2, password2=self.getUsernamePassword()
        user_uri2=self._create_user(username2,password2)
        client2=NMTKClient(self.site_url)
        client2.login(username=username2,
                      password=password2)
        filename=self.get_support_file('test1.geojson')
        test_file=client.uploadData(filename, 
                                    description='Test data file (MSP)')
        logger.debug('URI of test file is %s', test_file)
        
        tool_url=client.getURL('api','tool/')
        job_url=client.getURL('api','job/')
        response=client.get(tool_url, params={'format': 'json'})
        tools=response.json()['objects']
        # Get a list of all the Tool Resource URIs for Minnesota models,
        # since the test1.geojson file is a MN model-specific data file.
        for tool in tools:
            if 'minnesota' in tool['name'].lower():
                tool_uri=tool['resource_uri']
                break
        data={'tool': client.neuter_url(tool_uri),
              'data_file': client.neuter_url(test_file)}
        
        response=client.post(job_url, 
                             data=json.dumps(data),
                             headers={'Content-Type': 'application/json',})
        self.assertEqual(response.status_code, 201,
                         ('Expected job to be created - ' +
                          'got back %s instead') % (response.status_code,))
        job_uri=response.headers['location']
        # Now we have a job, let's get the form, generate the response, and
        # submit it back to the user.
        response=client2.get(job_uri, params={'format': 'json'})
        self.assertEqual(response.status_code, 401,
                         'Expected client2 to get a 401, not %s' % 
                         (response.status_code,))
        