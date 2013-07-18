from tests.utils.NMTKTestCase import NMTKTestCase
from tests.utils.client import NMTKClient
import logging
import simplejson as json
import subprocess
import mimetypes
import os
import time
logger=logging.getLogger(__name__)

class TestFileUpload(NMTKTestCase):
    
    def setUp(self):
        super(TestFileUpload, self).setUp()
        
    def tearDown(self):
        super(TestFileUpload, self).tearDown()
        
    def upload_file(self, client, filename, description=None,
                    payload={}):
        file_data=open(self.get_support_file(filename),'r')
        if description is not None:
            payload['description']=description
        fn=os.path.basename(filename)
        content_type=mimetypes.guess_type(fn)[0]
        files=[('file', (fn, file_data, content_type)),]
        response=client.post(self.api_file_url, data=payload, 
                             files=files)
        return response
    
    def test_basic_large_zipped_shapefile_upload(self):
        '''
        Test the upload and processing of a large zipped shapefile
        '''
        json_file=open(self.get_support_file('large_shapefile.zip'),'r')
        username, password=self.getUsernamePassword()
        user_uri=self._create_user(username,password)
        client=NMTKClient(self.site_url)
        client.login(username=username,
                     password=password)
        files=[('file', ('test1.json', json_file, 'application/json')),]
        response=client.post(self.api_file_url, files=files)
        logger.debug('Response from POST was %s', response)
        self.assertEqual(response.status_code, 201)
        data_file_url=response.headers['location']
        logger.debug('Response was %s', response.status_code)
        logger.debug('Location of data file is %s', data_file_url)
        
        end=time.time() + 60*2 # 2 minutes for processing
        while time.time() < end :
            response=client.get(data_file_url,
                                params={'format': 'json'})
            if response.json()['status'] == 'Import Complete':
                break
            time.sleep(1)
        self.assertEqual(response.json()['status'],
                         'Import Complete',
                         'Expected import to successfully complete within 120 seconds')

    def test_basic_different_srid_shapefile_upload(self):
        '''
        Test the upload and processing of a non standard shapefile (different EPSG)
        '''
        json_file=open(self.get_support_file('odd_srid_shapefile.zip'),'r')
        username, password=self.getUsernamePassword()
        user_uri=self._create_user(username,password)
        client=NMTKClient(self.site_url)
        client.login(username=username,
                     password=password)
        files=[('file', ('test1.json', json_file, 'application/json')),]
        response=client.post(self.api_file_url, files=files)
        logger.debug('Response from POST was %s', response)
        self.assertEqual(response.status_code, 201)
        data_file_url=response.headers['location']
        logger.debug('Response was %s', response.status_code)
        logger.debug('Location of data file is %s', data_file_url)
        
        end=time.time() + 60*2 # 2 minutes for processing
        while time.time() < end :
            response=client.get(data_file_url,
                                params={'format': 'json'})
            if response.json()['status'] == 'Import Complete':
                break
            time.sleep(1)
        self.assertEqual(response.json()['status'],
                         'Import Complete',
                         'Expected import to successfully complete within 120 seconds')

    def test_post_upload_delete_of_datafile(self):
        '''
        Test the ability to delete an uploaded file
        '''
        json_file=open(self.get_support_file('odd_srid_shapefile.zip'),'r')
        username, password=self.getUsernamePassword()
        user_uri=self._create_user(username,password)
        client=NMTKClient(self.site_url)
        client.login(username=username,
                     password=password)
        files=[('file', ('shapefile.zip', json_file, 'application/zip')),]
        response=client.post(self.api_file_url, files=files)
        logger.debug('Response from POST was %s', response)
        self.assertEqual(response.status_code, 201)
        data_file_url=response.headers['location']
        logger.debug('Response was %s', response.status_code)
        logger.debug('Location of data file is %s', data_file_url)
        
        end=time.time() + 60*2 # 2 minutes for processing
        while time.time() < end :
            response=client.get(data_file_url,
                                params={'format': 'json'})
            if response.json()['status'] == 'Import Complete':
                break
            time.sleep(1)
        self.assertEqual(response.json()['status'],
                         'Import Complete',
                         'Expected import to successfully complete within 120 seconds')    
        response=client.delete(data_file_url)
        logger.debug('Delete of file returned %s', response.status_code)
        self.assertEqual(response.status_code, 204,
                         'Expected response code of 204, not %s' % (response.status_code))
        
        response=client.get(data_file_url)
        self.assertEqual(response.status_code, 404,
                         'Expected response code of 404, not %s' % (response.status_code))
       
    def test_basic_json_upload(self):
        '''
        Test the upload and processing of a basic json file
        '''
        json_file=open(self.get_support_file('test1.geojson'),'r')
        username, password=self.getUsernamePassword()
        user_uri=self._create_user(username,password)
        client=NMTKClient(self.site_url)
        client.login(username=username,
                     password=password)
        files=[('file', ('test1.json', json_file, 'application/json')),]
        response=client.post(self.api_file_url, files=files)
        logger.debug('Response from POST was %s', response)
        self.assertEqual(response.status_code, 201)
        data_file_url=response.headers['location']
        logger.debug('Response was %s', response.status_code)
        logger.debug('Location of data file is %s', data_file_url)
        
        end=time.time() + 60*2 # 2 minutes for processing
        while time.time() < end :
            response=client.get(data_file_url,
                                params={'format': 'json'})
            if response.json()['status'] == 'Import Complete':
                break
            time.sleep(1)
        self.assertEqual(response.json()['status'],
                         'Import Complete',
                         'Expected import to successfully complete within 120 seconds')
        
    def test_file_upload_with_description(self):
        '''
        Verify that files can be uploaded with a description
        '''
        username, password=self.getUsernamePassword()
        user_uri=self._create_user(username,password)
        client=NMTKClient(self.site_url)
        client.login(username=username,
                     password=password)
        description='Test upload file description'
        response=self.upload_file(client, 
                                  'test1.geojson',
                                  description)
        logger.debug('Location for uploaded file is %s', 
                     response.headers['location'])
        loc=response.headers['location']
        
        response=client.get(loc, params={'format': 'json'})
        logger.debug(response.text)
        self.assertEqual(response.json()['description'],description,
                         'Expected uploaded description to be present')
        
    def test_file_upload_with_srid(self):
        '''
        Verify that files can be uploaded with an SRID
        '''
        username, password=self.getUsernamePassword()
        user_uri=self._create_user(username,password)
        client=NMTKClient(self.site_url)
        client.login(username=username,
                     password=password)
        description='Test upload file description'
        srid=3857
        response=self.upload_file(client, 
                                  'test1.geojson',
                                  description, payload={'srid': srid})
        logger.debug('Location for uploaded file is %s', 
                     response.headers['location'])
        data_file_url=response.headers['location']
        
        response=client.get(data_file_url, params={'format': 'json'})
        logger.debug(response.text)
        json_data=response.json()
        self.assertEqual(json_data['description'],description,
                         'Expected uploaded description to be present')
        self.assertEqual(json_data['srid'], srid,
                         'Expected SRID to be %s' % (srid,))
        # Verify the processing completes
        end=time.time() + 60*2 # 2 minutes for processing
        while time.time() < end :
            response=client.get(data_file_url,
                                params={'format': 'json'})
            if response.json()['status'] == 'Import Complete':
                break
            time.sleep(1)
        self.assertEqual(response.json()['status'],
                         'Import Complete',
                         'Expected import to successfully complete within 120 seconds')
        
        # Get the data again and make sure the SRID provided was used, and 
        # preserved.
        response=client.get(data_file_url, params={'format': 'json'})
        json_data=response.json()
        logger.debug('Response was %s', json_data)
        self.assertEqual(json_data['description'],description,
                         'Expected uploaded description to be present')
        self.assertEqual(json_data['srid'], srid,
                         'Expected SRID to be %s' % (srid,))
        
        
    