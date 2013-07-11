import unittest
import os
import simplejson as json
from tests.utils.client import NMTKClient
import logging
import subprocess
import string
import random
logger=logging.getLogger(__name__)


# Get some basic data..
base_path=os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       '../..'))
nmtk_path=os.environ.setdefault('NMTK_PATH', base_path)



class NMTKTestCase(unittest.TestCase):
    def _id_generator(self, size=6, 
                      chars=(string.ascii_lowercase + 
                             string.ascii_uppercase + 
                             string.digits)):
        return ''.join(random.choice(chars) for x in range(size))
    
    def getUsernamePassword(self):
        return (self._id_generator(), self._id_generator())
    
    def _getSiteConfigDynamic(self):
        try:
            command=['python',
                     self.settings_command,
                     'create_config']
            proc=subprocess.Popen(command, stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE)
            out,err=proc.communicate()
            config=json.loads(err)
            self.delusers.append(config['username'])
            # Stderr contains the config output.
            return config
        except Exception, e:
            logger.exception('Failed to get dynamic config!')
            
        return None
        
    def _getSiteConfigStatic(self):
        config_file=os.path.join(nmtk_path, 'tests/config.json')
        if os.path.exists(config_file):
            try:
                config=json.loads(open(config_file).read())
                return config
            except:
                pass
        return None
    
    def _getSiteConfig(self):
        config=self._getSiteConfigDynamic() or self._getSiteConfigStatic()
        if config:
            return config
        raise Exception('No valid config found (tried both dynamic and static')
        
    def setUp(self):
        self.settings_command=os.path.join(nmtk_path, 
                                           'NMTK_apps/manage.py')
        self.delusers=[]
        config=self._getSiteConfig()
        
        self.support_files=os.path.join(nmtk_path,'tests/support_files')
        self.site_url=config['site_url']
        self.username=config['username']
        self.password=config['password']
        self.client=NMTKClient(self.site_url)
        self.client.login(self.username, self.password)
        self.api_user_url=self.client.getURL('api','user/')
        self.api_file_url=self.client.getURL('api','datafile/')
        
        
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
        
    def _create_user(self, *args, **kwargs):
        '''
        A helper method to create a new user, given a password and userid
        '''
        if len(args) == 2:
            kwargs['username']=args[0]
            kwargs['password']=args[1]
        for key in ('username','password'):
            kwargs.setdefault(key, self._id_generator())
        
        response=self.client.create_user(**kwargs)
        self.delusers.append(kwargs['username'])
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