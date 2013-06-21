# Note that PYTHONPATH here must be set to the
# root directory of the GIT environment
#import sys
#from subprocess import call
#sys.path.insert(0, call(['git', 'rev-parse', '--show-toplevel']))
from tests.utils.NMTKTestCase import NMTKTestCase
from tests.utils.client import NMTKClient

class TestLoginAndLogout(NMTKTestCase):
    def setUp(self):
        super(TestLoginAndLogout, self).setUp()
        
        
    def test_login_verify(self):
        client=NMTKClient(self.site_url)
        result=client.login(self.username, self.password)
        # Verify that we logged in successfully by checking the status code
        self.assertEqual(result.status_code, 302)
        
    def test_logout_verify(self):
        client=NMTKClient(self.site_url)
        result=client.login(self.username, self.password)
        self.assertEqual(result.status_code, 302)
        result=client.logout()
        self.assertEqual(result.status_code, 302)
        result=client.get(client.getURL(path='/server/'),
                          allow_redirects=False)
        login_url=client.getURL('login')[:-1]
        if not result.headers['location'].startswith(login_url):
            self.fail('Got login redirect to here: %s' % result.headers['location'])
        self.assertEqual(result.status_code, 302)
        