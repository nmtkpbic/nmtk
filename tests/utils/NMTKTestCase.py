import unittest
import os
import simplejson as json


# Get some basic data..
base_path=os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       '../..'))
nmtk_path=os.environ.setdefault('NMTK_PATH', base_path)
settings_command=os.path.join(nmtk_path, 
                              'NMTK_apps/manage.py')
config_file=os.path.join(nmtk_path, 'tests/config.json')

class NMTKTestCase(unittest.TestCase):
    
    def setUp(self):
        config=json.loads(open(config_file).read())
        self.site_url=config['site_url']
        self.username=config['username']
        self.password=config['password']
        
        
if __name__ == '__main__':
    site_url=raw_input('Enter the URL: ').strip()
    username=raw_input('Enter the username: ').strip()
    password=raw_input('Enter the password: ').strip()
    data={'site_url': site_url,
          'username': username,
          'password': password }
    data2=json.dumps(data)
    open(config_file,'w').write(data2)