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


import requests
import simplejson as json
import logging
import os
import time
import urlparse
import mimetypes
logger=logging.getLogger(__name__)

class NMTKClientException(Exception): pass


class NMTKClient(object):
    '''
    A sample client that is both used to test the API, as well as for users and
    third parties that wish to interact with the API. It uses the python requests
    module, but should be fairly straightforward to implement in a number of 
    different languages.
    '''
    default_request_args={'allow_redirects': False,
                          'verify': False, }
    def getURL(self, named_url=None, path=None):
        '''
        Given a URL by name, retrieve the full URL for that partictular view.
        This allows us to name specific things, like API paths and whatnot
        just once and have them change later as needed.
        
        If path is provided it is assumed that the caller is providing a URL
        path.  If the path starts with a '/' it is assumed it is an absolute 
        path.  Otherwise it is relative to base_url
        '''
        base_url='/server/'
        named_urls={'login': 'login/',
                    'logout': 'logout/',
                    'api': 'api/v1/'}
        if path is not None and path.startswith('/'):
            if named_url:
                logger.warning('Named URLs (%s) are ignored when used in ' +
                               'in conjunction with an absolute path (%s)',
                                named_url, path)
            url='%s%s' % (self.site_url, path)
        elif named_url and path is None:
            url='%s%s%s' % (self.site_url, base_url, 
                            named_urls.get(named_url))
        elif named_url and path is not None:
            url='%s%s%s%s' % (self.site_url, base_url, 
                              named_urls.get(named_url),
                              path)
        elif path is not None:
            url='%s%s%s' % (self.site_url, base_url, path)
        else:
            raise NMTKClientException('No path or named url provided')
        if not url.endswith('/'):
            url='%s/' % (url,)
        logger.debug('Returning requested URL: %s', url)
        return url
        
    def __init__(self, site_url):
        if site_url.endswith('/'):   
            self.site_url=site_url[:-1]
        else:
            self.site_url=site_url
        parts=urlparse.urlparse(self.site_url)
        self.base_url=urlparse.urlunparse((parts[0],parts[1],'','','',''))
        # Store a session so we can persist things.
        self.request=requests.Session()
        
    def post(self, *args, **kwargs):
        return self.request.post(*args, **kwargs)
    
    def put(self, *args, **kwargs):
        return self.request.put(*args, **kwargs)
    
    def get(self, *args, **kwargs):
        default_args=self.default_request_args.copy()
        default_args.update(kwargs)
        return self.request.get(*args, **default_args)
    
    def delete(self, *args, **kwargs):
        return self.request.delete(*args, **kwargs)
    
    def login(self, username, password):
        '''
        Get a CSRF token and set it as a cookie so we can bypass CSRF
        protection checks that exist in the code.  Then log the user in.
        '''
        self.request.get(self.getURL('login'))
        csrf_token=self.request.cookies['csrftoken']
        self.request.headers.update({'X-CSRFToken': csrf_token})
        # Now log in...
        return self.request.post(self.getURL('login'), allow_redirects=False,
                                 data={'username': username,
                                       'password': password,
                                       'next': self.getURL(path='')})
        
    def uploadData(self, filename, description=None,
                   srid=None, timeout=None):
        '''
        Upload data into NMTK via the API using the provided description
        and/or SRID data.  If timeout is 0/None then wait forever for completion.
        If timeout is -1, return the location of the new resource immediately.
        If timeout is any other integer value, then wait that long for the 
        file to be uploaded.
        '''
        payload={}
        file_data=open(filename,'r')
        if description is not None:
            payload['description']=description
        if srid is not None:
            payload['srid']=srid
        fn=os.path.basename(filename)
        content_type=mimetypes.guess_type(fn)[0]
        files=[('file', (fn, file_data, content_type)),]
        api_file_url=self.getURL('api', 'datafile/')
        response=self.post(api_file_url, data=payload, 
                           files=files)
        if response.status_code <> 201:
            raise NMTKClientException('File upload failed: %s',
                                      response.text)
        upload_uri=response.headers['location']
        if timeout == -1:
            return upload_uri
        end=time.time() + (timeout or 0) # 2 minutes for processing
        while (not timeout) or (time.time() < end) :
            response=self.get(upload_uri,
                              params={'format': 'json'})
            if response.json()['status'] == 'Import Complete':
                break
            time.sleep(.5)
        else:
            raise NMTKClientException('Upload failed to complete: %s',
                                      upload_uri, response.status_code)
        
        return upload_uri
    
    def neuter_url(self, url):
        '''
        given a full URL (with http, etc.) return just the portion that would
        represent the path to the URI
        '''
        if url.startswith(self.base_url):
            return url[len(self.base_url):]
        return url
    
    def logout(self):
        return self.request.get(self.getURL('logout'),
                                allow_redirects=False,)
        
    def create_user(self, username, password, **kwargs):
        '''
        A helper method to create a new user, given a password and userid
        '''
        data={'username': username,
              'password': password,
              'email': 'test@nmtk.otg-nc.com'}
        data.update(kwargs)
        response=self.post(self.getURL('api','user/'),
                           data=json.dumps(data),
                           headers={'Content-Type': 'application/json',})
        logger.debug('Response from create user request was %s', 
                     response.status_code)
        if response.status_code <> 201:
            logger.debug('Response from user create was %s', response.text)
        # Status code of 201 means it got created.
        logger.debug('HTTP Result was %s', response.headers.get('location'))
        return response

if __name__ == '__main__':
    import sys
    FORMAT='%(asctime)-15s - %(module)s(%(lineno)d): %(message)s'
    logging.basicConfig(format=FORMAT, stream=sys.stderr)
    logger.setLevel(logging.DEBUG)
    
    client=NMTKClient('http://nmtk.otg-nc.com/')
    logger.debug('Attempting to test a login for a user.')
    r=client.login('chander','chander')
    logger.info('Login complete, redirected to %s (%s)', r.headers['location'],
                r.status_code)
    r=client.logout()
    logger.info('Logout complete, redirected to %s (%s)', r.headers['location'],
                r.status_code)
    
    