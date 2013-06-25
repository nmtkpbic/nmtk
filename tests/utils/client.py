import requests
import logging
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
        
    def logout(self):
        return self.request.get(self.getURL('logout'),
                                allow_redirects=False,)

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
    
    