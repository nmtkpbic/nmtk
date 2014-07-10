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
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# Note that PYTHONPATH here must be set to the
# root directory of the GIT environment
#import sys
#from subprocess import call
#sys.path.insert(0, call(['git', 'rev-parse', '--show-toplevel']))
from tests.utils.NMTKTestCase import NMTKTestCase
from tests.utils.client import NMTKClient
import logging
logger=logging.getLogger(__name__)

class TestLoginAndLogout(NMTKTestCase):

    def test_login_verify(self):
        '''
        Verify we can successfully log into the site.
        Tests that the client works properly, sets the right CSRF headers,
        and that the server accepts a login properly.
        '''
        client=NMTKClient(self.site_url)
        result=client.login(self.username, self.password)
        # Verify that we logged in successfully by checking the status code
        self.assertEqual(result.status_code, 302)
        
    def test_logout_verify(self):
        '''
        Verify that we can log out successfully.
        Verifies that logout functionality works, and that the server
        properly invalidates the session when logout is requested.  Verify
        that the correct redirect URL is provided for login after a user has
        logged out.
        '''
        
        client=NMTKClient(self.site_url)
        test_url='%s%s' % (client.getURL('api'),
                           'job/')
        result=client.login(self.username, self.password)
        self.assertEqual(result.status_code, 302)
        result=client.get(test_url, params={'format': 'json'})
        self.assertEqual(result.status_code, 200)
        result=client.logout()
        self.assertEqual(result.status_code, 302)
        login_url=client.getURL('login')[:-1]
        
        result=client.get(test_url, params={'format': 'json'})
        self.assertEqual(result.status_code, 401)
        