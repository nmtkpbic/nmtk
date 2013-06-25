import unittest
import os
import simplejson as json
from tests.utils.client import NMTKClient
import logging
import subprocess
logger=logging.getLogger(__name__)


# Get some basic data..
base_path=os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       '../..'))
nmtk_path=os.environ.setdefault('NMTK_PATH', base_path)

config_file=os.path.join(nmtk_path, 'tests/config.json')

class NMTKTestCase(unittest.TestCase):
    
    def setUp(self):
        config=json.loads(open(config_file).read())
        self.support_files=os.path.join(nmtk_path,'tests/support_files')
        self.site_url=config['site_url']
        self.username=config['username']
        self.password=config['password']
        self.settings_command=os.path.join(nmtk_path, 
                                           'NMTK_apps/manage.py')
        self.client=NMTKClient(self.site_url)
        self.client.login(self.username, self.password)
        self.api_user_url=self.client.getURL('api','user/')
        self.api_file_url=self.client.getURL('api','datafile/')
        self.delusers=[]
        
    def get_support_file(self, fn):
        return os.path.join(self.support_files, fn)
    
    def tearDown(self):
        '''
        Use the management purge_users command to purge the users created
        during testing from the database.
        '''
        if self.delusers:
            command=['python',
                     self.settings_command,
                     'purge_users'] + self.delusers
            with open(os.devnull, "w") as fnull:
                subprocess.call(command, stdout=fnull, stderr=fnull)
        
    def _create_user(self, username, password, **kwargs):
        '''
        A helper method to create a new user, given a password and userid
        '''
        data={'username': username,
              'password': password}
        data.update(kwargs)
        response=self.client.post(self.api_user_url,
                                  data=json.dumps(data),
                                  headers={'Content-Type': 'application/json',})
        logger.debug('Response from create user request was %s', 
                     response.status_code)
        if response.status_code <> 201:
            logger.debug('Response from user create was %s', response.text)
        # Status code of 201 means it got created.
        logger.debug('HTTP Result was %s', response.headers.get('location'))
        self.delusers.append(username)
        return response
        
    def _delete_user(self, url):
        response=self.client.delete(url)
        logger.debug('Deleted %s with status code of %s',
                     url, response.status_code)
        return response
        
        
if __name__ == '__main__':
    site_url=raw_input('Enter the URL: ').strip()
    username=raw_input('Enter the username: ').strip()
    password=raw_input('Enter the password: ').strip()
    data={'site_url': site_url,
          'username': username,
          'password': password }
    data2=json.dumps(data)
    open(config_file,'w').write(data2)