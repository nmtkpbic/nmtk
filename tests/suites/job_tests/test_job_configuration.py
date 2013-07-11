from tests.utils.NMTKTestCase import NMTKTestCase
from tests.utils.client import NMTKClient
import logging
import simplejson as json
import os
import time
logger=logging.getLogger(__name__)

class TestJobConfiguration(NMTKTestCase):
    
    def setUp(self):
        super(TestJobConfiguration, self).setUp()
        
    def tearDown(self):
        super(TestJobConfiguration, self).tearDown()
        
    def test_setup_job(self):
        username, password=self.getUsernamePassword()
        user_uri=self._create_user(username,password)
        client=NMTKClient(self.site_url)
        response=client.login(username=username,
                              password=password)
        filename=self.get_support_file('test1.geojson')
        test_file=client.uploadData(filename, 
                                    description='Test configuration file')
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
            self.assertTrue(len(data.get('form','')) > 10, 'Expected the form to appear in' +
                            'the output JSON (got %s)' % (response.text,))
    
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

