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
logger = logging.getLogger(__name__)


class TestToolList(NMTKTestCase):

    def setUp(self):
        super(TestToolList, self).setUp()

    def tearDown(self):
        super(TestToolList, self).tearDown()

    def test_list_tools(self):
        '''
        Verify that any user (even without login) can retrieve a list of tools.
        '''
        username, password = self.getUsernamePassword()
        user_uri = self._create_user(username, password)
        client = NMTKClient(self.site_url)
        tool_url = client.getURL('api', 'tool/')
        logger.debug('Attempting to get tool list (%s) as not-logged-in user',
                     tool_url)
        response = client.get(tool_url, params={'format': 'json'})
        self.assertEqual(200, response.status_code,
                         'expected 200, not %s' % (response.status_code,))
        response = client.login(username=username,
                                password=password)
        response = client.get(tool_url, params={'format': 'json'})
        self.assertEqual(200, response.status_code,
                         'expected 200 (when logged in), not %s' %
                         (response.status_code,))
        jsdata = response.json()
        self.assertEqual(min(jsdata['meta']['total_count'],
                             jsdata['meta']['limit']), len(jsdata['objects']),
                         'Expected the number of objects returned to match the purported count!')
