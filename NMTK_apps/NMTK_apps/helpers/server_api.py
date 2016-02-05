# 2013 - Chander Ganesan <chander@otg-nc.com>
#
# 2013-01-02 NMTK class used for basic server communication.
#            This will (mostly) add the appropriate headers, etc.
#            as required for communication with the NTMK server.
#
import requests
import json
import hmac
import hashlib
import logging
import datetime
from django.utils import timezone
logger = logging.getLogger(__name__)


class NMTKAPIException(Exception):
    pass


def json_custom_serializer(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return str(obj)
    else:
        raise TypeError(
            "Unserializable object {} of type {}".format(obj, type(obj))
        )


class NMTKClient(object):

    '''
    This client class is designed to perform the basic operations
    related to communicating with the NMTK server.

    In general, a json_payload is a payload that is already encoded in
    the json format.  A "payload" is a payload that requires encoding to
    the json format.
    '''

    def __init__(self, url, tool_server_id=None,
                 shared_secret=None,
                 job_id=None,
                 verify_ssl=True):
        '''
        Since it's likely the caller will have the public/private keys already
        loaded up, we'll require either them, or a filename containing them.
        '''
        self.verify_ssl = verify_ssl
        self.url = url.rstrip(
            '/')  # Remove the trailing slash if there is one..
        try:
            self.tool_server_id = tool_server_id
            self.shared_secret = shared_secret
        except Exception as e:
            raise Exception(
                'A private and public key must be provided somehow.')
        self.job_id = job_id or self.tool_server_id

    def _getSignature(self, payload):
        '''
        Generate an HMAC signature for the entire payload using the
        private key of the application.  This'll go in the
        HTTP protocol standard authorization header.
        '''
        logger.debug("%s: %s", type(payload), payload)
        logger.debug('Signature key is %s', self.shared_secret)
        digest_maker = hmac.new(str(self.shared_secret),
                                payload,
                                hashlib.sha1)
        digest = digest_maker.hexdigest()
        return digest

    def _generate_request(self, url, payload, type="post", files=None,
                          headers={}):
        if files is None:
            files = {}
        if 'config' in files.keys():
            logger.debug('Data is %s', files['config'])
            raise NMTKAPIException('Reserved word "config" found in response')
        payload['job'] = {'timestamp': datetime.datetime.now().isoformat(),
                          'job_id': self.job_id,
                          'tool_server_id': self.tool_server_id}
        payload_json = json.dumps(payload, default=json_custom_serializer)
        signature = self._getSignature(payload_json)
        headers.update({'authorization': signature,
                        'Referer': url})
        # We use the requests library here - it'll do the correct
        # requests using requests.post, requests.get, requests.put
        # so the getattr(requests,type) uses the type provided to
        # perform the proper request operation to the NMTK server.
        files['config'] = ('config', payload_json,)

        logger.debug(files)
        r = getattr(requests, type)(url,
                                    files=files,
                                    headers=headers,
                                    verify=self.verify_ssl)
        r.raise_for_status()
        # Note that everything from the server comes back as a JSON response,
        # so we always decode and return that response.
        return r.json()

    def updateResults(self, result_field=None, result_file=None, units=None,
                      files={}, failure=False, payload={}):
        '''
        There are two methods the analysis tool uses to communicate with the
        server - one of which is analyses/results (a URL).  This is used
        to send final results back to the server.

        Note: files should be a dictionary of two-tuples, containing a file name and
              a file-like object.  the key of the dictionary is the name of the POST
              field used to send the file, and at least one of those keys should match
              the 'result_field' value.
        '''
        url = "%s/%s" % (self.url, "tools/result",)
        if failure:
            payload['status'] = 'error'
        else:
            payload['status'] = 'results'
            payload['results'] = {'field': result_field,
                                  'file': result_file,
                                  'units': units}

        result = self._generate_request(url, payload, "post", files=files)
        return result['status']

    def updateStatus(self, status, category='Status', timestamp=None):
        '''
        There are two methods the analysis tool uses to communicate with the
        server - one of which is analyses/update (a URL).  This is used
        to send status updates back to the server.
        '''
        url = "%s/%s" % (self.url, "tools/update",)
        payload = {'status': status,
                   'category': category,
                   'timestamp': timezone.now().isoformat()}

        logger.debug("Logging result to %s", url)
        logger.debug('Payload is %s', payload)
        result = self._generate_request(url, payload, "post")
        logger.debug('Response from status update is %s', result)
        return result['status']
