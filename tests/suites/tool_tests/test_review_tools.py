from tests.utils.NMTKTestCase import NMTKTestCase
from tests.utils.client import NMTKClient
import logging
import simplejson as json
import os
import time
logger=logging.getLogger(__name__)

class TestToolList(NMTKTestCase):
    
    def setUp(self):
        super(TestToolList, self).setUp()
        
    def tearDown(self):
        super(TestToolList, self).tearDown()
        
    def test_list_tools(self):
        username, password=self.getUsernamePassword()
        user_uri=self._create_user(username,password)
        client=NMTKClient(self.site_url)
        tool_url=client.getURL('api','tool/')
        logger.debug('Attempting to get tool list (%s) as not-logged-in user',
                     tool_url)
        response=client.get(tool_url, params={'format': 'json'})
        self.assertEqual(401, response.status_code,
                         'expected 401, not %s' % (response.status_code,))
        response=client.login(username=username,
                              password=password)
        response=client.get(tool_url, params={'format': 'json'})
        self.assertEqual(200, response.status_code,
                         'expected 200 (when logged in), not %s' % 
                         (response.status_code,))
        jsdata=response.json()
        self.assertEqual(min(jsdata['meta']['total_count'],
                             jsdata['meta']['limit']), len(jsdata['objects']),
                             'Expected the number of objects returned to match the purported count!')
    

        
    