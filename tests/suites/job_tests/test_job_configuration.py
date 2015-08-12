#!/usr/bin/env python
# Non-Motorized Toolkit
# Copyright (c) 2014 Open Technology Group Inc. (A North Carolina Corporation)
# Developed under Federal Highway Administration (FHWA) Contracts:
# DTFH61-12-P-00147 and DTFH61-14-P-00108
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer
#       in the documentation and/or other materials provided with the distribution.
#     * Neither the name of the Open Technology Group, the name of the
#       Federal Highway Administration (FHWA), nor the names of any
#       other contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# Open Technology Group Inc BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
# USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
from tests.utils.NMTKTestCase import NMTKTestCase
from tests.utils.client import NMTKClient
import logging
import simplejson as json
import os
import time
from mechanize import ParseFile
import StringIO
logger = logging.getLogger(__name__)


class TestJobConfiguration(NMTKTestCase):

    def setUp(self):
        super(TestJobConfiguration, self).setUp()

    def tearDown(self):
        '''
        TearDown
        '''
        super(TestJobConfiguration, self).tearDown()

    def test_setup_job(self):
        '''
        Upload and supply a data file for some jobs, then verify the form comes back.
        '''
        username, password = self.getUsernamePassword()
        user_uri = self._create_user(username, password)
        client = NMTKClient(self.site_url)
        response = client.login(username=username,
                                password=password)
        filename = self.get_support_file('test1.geojson')
        test_file = client.uploadData(filename,
                                      description='Test data file (MSP)')
        logger.debug('URI of test file is %s', test_file)

        tool_url = client.getURL('api', 'tool/')
        job_url = client.getURL('api', 'job/')
        response = client.get(tool_url, params={'format': 'json'})
        tools = response.json()['objects']
        tool_uri_list = []
        # Get a list of all the Tool Resource URIs for Minnesota models,
        # since the test1.geojson file is a MN model-specific data file.
        for tool in tools:
            if 'minnesota' in tool['name'].lower():
                tool_uri_list.append(tool['resource_uri'])
        job_uri_list = []
        for uri in tool_uri_list:
            data = {'tool': client.neuter_url(uri),
                    'data_file': client.neuter_url(test_file)}
            response = client.post(
                job_url, data=json.dumps(data), headers={
                    'Content-Type': 'application/json', })
            self.assertEqual(response.status_code, 201,
                             ('Expected job to be created - ' +
                              'got back %s instead') % (
                                 response.status_code))
            logger.debug('Created new job entry with URI %s',
                         response.headers['location'])
            job_uri_list.append(response.headers['location'])
        for uri in job_uri_list:
            response = client.get(uri, params={'format': 'json'})
            data = response.json()
            self.assertTrue(len(json.dumps(data.get('form', ''))) > 10,
                            'Expected the form to appear in' +
                            'the output JSON (got %s)' % (response.text,))

    def test_submit_job(self):
        '''
        Verify that we can properly submit a job (form) via the API and \
get back the (eventual) results and status of the running job.  Also ensure other \
users cannot download results.
        '''
        username, password = self.getUsernamePassword()
        user_uri = self._create_user(username, password)
        client = NMTKClient(self.site_url)
        response = client.login(username=username,
                                password=password)
        filename = self.get_support_file('test1.geojson')
        test_file = client.uploadData(filename,
                                      description='Test data file (MSP)')
        logger.debug('URI of test file is %s', test_file)

        tool_url = client.getURL('api', 'tool/')
        job_url = client.getURL('api', 'job/')
        response = client.get(tool_url, params={'format': 'json'})
        tools = response.json()['objects']

        # Get a list of all the Tool Resource URIs for Minnesota models,
        # since the test1.geojson file is a MN model-specific data file.
        for tool in tools:
            if 'umn' in tool['name'].lower():
                tool_uri = tool['resource_uri']
                break
        data = {'tool': client.neuter_url(tool_uri),
                'description': 'Test job for testing by the automated test!'}

        response = client.post(job_url,
                               data=json.dumps(data),
                               headers={'Content-Type': 'application/json', })
        #logger.debug('Result from post was %s', response.text)
        self.assertEqual(response.status_code, 201,
                         ('Expected job to be created - ' +
                          'got back %s instead') % (response.status_code,))
        job_uri = response.headers['location']

        # Now we have a job, let's get the form, generate the response, and
        # submit it back to the user.
        payload = {"config": {"coefficients": {"Arterial_coeff": {"type": "number",
                                                                  "value": 391.8},
                                               "BusRoute_coeff": {"type": "number",
                                                                  "value": 100.3},
                                               "CBDdist_km_coeff": {"type": "number",
                                                                    "value": -40.3},
                                               "Collector_coeff": {"type": "number",
                                                                   "value": 611.1},
                                               "Crime_coeff": {"type": "number",
                                                               "value": 2.9},
                                               "EmployAccess_coeff": {"type": "number",
                                                                      "value": 0},
                                               "LUMix_coeff": {"type": "number",
                                                               "value": -919.9},
                                               "MedHHInc_coeff": {"type": "number",
                                                                  "value": 2.1},
                                               "OffstreetTrail_coeff": {"type": "number",
                                                                        "value": 253.8},
                                               "PDperkm2_coeff": {"type": "number",
                                                                  "value": -0.035},
                                               "PctU5_O65_coeff": {"type": "number",
                                                                   "value": 32.5},
                                               "Pctnonwhite_coeff": {"type": "number",
                                                                     "value": -29.8},
                                               "Pctw4ormore_coeff": {"type": "number",
                                                                     "value": 371.4},
                                               "Precip_coeff": {"type": "number",
                                                                "value": -127.8},
                                               "Principal_coeff": {"type": "number",
                                                                   "value": 66.4},
                                               "Tmax_coeff": {"type": "number",
                                                              "value": -26},
                                               "WatDist_km_coeff": {"type": "number",
                                                                    "value": -21.6},
                                               "Year_coeff": {"type": "number",
                                                              "value": -5.9},
                                               "constant": {"type": "number",
                                                            "value": 788.6}
                                               },
                              "data": {"Arterial": {"type": "property",
                                                    "value": "Arterial"},
                                       "BusRoute": {"type": "property",
                                                    "value": "BusRoute"},
                                       "CBDdist_km": {"type": "property",
                                                      "value": "CBDdist_km"},
                                       "Collector": {"type": "property",
                                                     "value": "Collector"},
                                       "Crime": {"type": "property",
                                                 "value": "Crime"},
                                       "EmployAccess": {"type": "property",
                                                        "value": "EmployAccess"},
                                       "LUMix": {"type": "property",
                                                 "value": "LUMix"},
                                       "MedHHInc": {"type": "property",
                                                    "value": "MedHHInc"},
                                       "OffstreetTrail": {"type": "property",
                                                          "value": "OffstreetTrail"},
                                       "PDperkm2": {"type": "property",
                                                    "value": "PDperkm2"},
                                       "PctU5_O65": {"type": "property",
                                                     "value": "PctU5_O65"},
                                       "Pctnonwhite": {"type": "property",
                                                       "value": "Pctnonwhite"},
                                       "Pctw4ormore": {"type": "property",
                                                       "value": "Pctw4ormore"},
                                       "Principal": {"type": "property",
                                                     "value": "Principal"},
                                       "WatDist_km": {"type": "property",
                                                      "value": "WatDist_km"}
                                       },
                              "results": {"result": {"type": "string",
                                                     "value": "ped12ols"}
                                          }
                              },
                   "file_config": {
            "data": test_file
        }
        }
        data = client.get(job_uri,
                          params={'format': 'json'}).json()
        data.update(payload)
        job_id = data['id']

        response = client.put(job_uri,
                              headers={'Content-Type': 'application/json', },
                              data=json.dumps(data))
        logger.debug('Response from job update was %s', response.text)
        self.assertTrue(response.status_code in (204, 202),
                        'Expected a return code of 204/202 with valid ' +
                        'data provided got (%s)' % (response.status_code))

        # Now check the status to wait for completion
        timeout = time.time() + 120
        status_url = client.getURL('api', 'job_status/')
        params = {'job': job_id,
                  'format': 'json',
                  'limit': 1}
        steps = ['Parameter & data file validation complete.', 'COMPLETE']
        prev_response = ''
        while time.time() < timeout:
            response = client.get(status_url, params=params)
            self.assertEqual(response.status_code, 200,
                             'Expected to get valid response back')
            if len(response.text):
                json_data = response.json()
                if prev_response != response.text:
                    logger.debug('Reponse changed to %s', response.text)
                prev_response = response.text
                if json_data['meta']['total_count']:
                    if json_data['objects'][0]['message'] in steps:
                        steps.remove(json_data['objects'][0]['message'])
                    if json_data['objects'][0]['message'] == 'COMPLETE':
                        break
            time.sleep(.1)
        self.assertEqual(len(steps), 0,
                         'Did not get expected message(s) %s' % (steps,))

        response = client.get(job_uri, params={'format': 'json'})
        json_response = response.json()
        self.assertTrue(
            json_response['status'] in (
                'Post-processing results',
                'Complete'),
            'Expected a status of Complete, not %s' %
            (json_response['status']))

        timeout = time.time() + 120
        while time.time() < timeout:
            if json_response['status'] == 'Complete':
                break
            response = client.get(job_uri, params={'format': 'json'})
            json_response = response.json()
            time.sleep(.1)
        else:
            self.fail(
                'Expected status to be complete after 120s timeout, not %s' %
                (json_response['status']))
        results_uri = None
        for row in json_response['results_files']:
            if row['primary']:
                logger.debug("Primary results were %s", row)
                results_uri = client.getURL(path=row['datafile'])
        if not results_uri:
            self.fail(
                'Expected to get back a primary result, none found in %s' %
                (json_response,))
        # Try to see if another user can download this job or results..
        username2, password2 = self.getUsernamePassword()
        user_uri = self._create_user(username2, password2)
        client2 = NMTKClient(self.site_url)
        client2.login(username=username2,
                      password=password2)
        response = client2.get(job_uri, params={'format': 'json'})
        self.assertEqual(
            response.status_code,
            401,
            ('Expected 401 forbidden when ' +
             'another user tried to get job info (not %s)') %
            (response.status_code,
             ))
        response = client2.get(results_uri,
                               params={'format': 'json'})
        self.assertEqual(
            response.status_code,
            401,
            ('Expected 401 forbidden when ' +
             'another user tried to get result (not %s)') %
            (response.status_code,
             ))

        response = client.get(results_uri,
                              params={'format': 'json'})
        self.assertEqual(
            response.status_code, 200, 'Status code expected was 200, not %s' %
            (response.status_code,))
        logger.debug('Header is %s', response.headers)

        data = json.loads(response.content)

    def test_prevent_user_from_using_other_user_data(self):
        '''
        Verify that one user can neither access, nor submit jobs, with another users data
        '''
        username, password = self.getUsernamePassword()
        user_uri = self._create_user(username, password)
        username2, password2 = self.getUsernamePassword()
        user_uri = self._create_user(username2, password2)
        client = NMTKClient(self.site_url)
        client.login(username=username,
                     password=password)
        client2 = NMTKClient(self.site_url)
        client2.login(username=username2,
                      password=password2)
        filename = self.get_support_file('test1.geojson')
        test_file = client.uploadData(filename,
                                      description='Test configuration file')
        # Just try to access the other users file
        response = client2.get(test_file, params={'format': 'json'})
        logger.debug('Response when getting other users file was %s',
                     response.status_code)
        self.assertEqual(response.status_code, 401,
                         'Expected a 401, got a %s' % (response.status_code,))
        # Try to create a job with the other users file
        job_url = client.getURL('api', 'job/')
        tool_url = client.getURL('api', 'tool/')

        response = client.get(tool_url, params={'format': 'json'})
        tools = response.json()['objects']
        # Get a list of all the Tool Resource URIs for Minnesota models,
        # since the test1.geojson file is a MN model-specific data file.
        for tool in tools:
            if 'umn' in tool['name'].lower():
                tool_uri = tool['resource_uri']
                break
        data = {'tool': client.neuter_url(tool_uri),
                'description': 'how now brown cow'}
        logger.debug(
            'Verifying that user A cannot create a job with User B data')
        response = client2.post(job_url,
                                data=json.dumps(data),
                                headers={'Content-Type': 'application/json', })
        logger.debug('Status code was %s', response.status_code)
        logger.debug('Response text was %s', response.text)

    def test_submit_job_other_user_denied_access(self):
        '''
        Verify that once a job is submitted/created, other users cannot access.
        '''
        username, password = self.getUsernamePassword()
        user_uri = self._create_user(username, password)
        client = NMTKClient(self.site_url)
        response = client.login(username=username,
                                password=password)
        username2, password2 = self.getUsernamePassword()
        user_uri2 = self._create_user(username2, password2)
        client2 = NMTKClient(self.site_url)
        client2.login(username=username2,
                      password=password2)
        filename = self.get_support_file('test1.geojson')
        test_file = client.uploadData(filename,
                                      description='Test data file (MSP)')
        logger.debug('URI of test file is %s', test_file)

        tool_url = client.getURL('api', 'tool/')
        job_url = client.getURL('api', 'job/')
        response = client.get(tool_url, params={'format': 'json'})
        tools = response.json()['objects']
        # Get a list of all the Tool Resource URIs for Minnesota models,
        # since the test1.geojson file is a MN model-specific data file.
        for tool in tools:
            if 'umn' in tool['name'].lower():
                tool_uri = tool['resource_uri']
                break
        data = {'tool': client.neuter_url(tool_uri),
                'description': 'how now brown cow'}

        response = client.post(job_url,
                               data=json.dumps(data),
                               headers={'Content-Type': 'application/json', })
        self.assertEqual(response.status_code, 201,
                         ('Expected job to be created - ' +
                          'got back %s instead') % (response.status_code,))
        job_uri = response.headers['location']
        # Now we have a job, let's get the form, generate the response, and
        # submit it back to the user.
        response = client2.get(job_uri, params={'format': 'json'})
        self.assertEqual(response.status_code, 401,
                         'Expected client2 to get a 401, not %s' %
                         (response.status_code,))
