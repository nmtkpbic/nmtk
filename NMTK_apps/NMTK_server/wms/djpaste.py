# (c) 2013 Chander Ganesan and contributors; written to work with Django and Paste (http://pythonpaste.org)
# Paste CGI "middleware" for Django by Chander Ganesan <chander@otg-nc.com>
# Open Technology Group, Inc <http://www.otg-nc.com>
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
import os
import sys
import subprocess
import urllib
try:
    import select
except ImportError:
    select = None

from paste.util import converters
from paste.cgiapp import *
from paste.cgiapp import StdinReader, proc_communicate
from paste.cgiapp import CGIApplication as PasteCGIApplication
import urllib
from django.http import HttpResponse
# Taken from http://plumberjack.blogspot.com/2009/09/how-to-treat-logger-like-output-stream.html
import logging
mod_logger=logging.getLogger(__name__)

class LoggerWriter:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message.strip() and message != '\n':
            self.logger.log(self.level, message)

class CGIApplication(PasteCGIApplication):
    def __call__(self, request, environ, logger=None):
        if not logger:
            self.logger=LoggerWriter(logging.getLogger(__name__), logging.ERROR)
        else:
            self.logger=logger
        if 'REQUEST_URI' not in environ:
            environ['REQUEST_URI'] = (
                urllib.quote(environ.get('SCRIPT_NAME', ''))
                + urllib.quote(environ.get('PATH_INFO', '')))
        if self.include_os_environ:
            cgi_environ = os.environ.copy()
        else:
            cgi_environ = {}
        for name in environ:
            # Should unicode values be encoded?
            if (name.upper() == name
                and isinstance(environ[name], str)):
                cgi_environ[name] = environ[name]
        if self.query_string is not None:
            old = cgi_environ.get('QUERY_STRING', '')
            if old:
                old += '&'
            cgi_environ['QUERY_STRING'] = old + self.query_string
        cgi_environ['SCRIPT_FILENAME'] = self.script
        proc = subprocess.Popen(
            [self.script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=cgi_environ,
            cwd=os.path.dirname(self.script),
            )
        writer = CGIWriter()
        if select and sys.platform != 'win32':
            proc_communicate(
                proc,
                stdin=request,
                stdout=writer,
                stderr=self.logger)
        else:
            stdout, stderr = proc.communicate(request.read())
            if stderr:
                 self.logger.write(stderr)
            writer.write(stdout)
        if not writer.headers_finished:
            return HttpResponse(status=400)
        return writer.response

class CGIWriter(object):

    def __init__(self):
        self.status = '200 OK'
        self.headers = []
        self.headers_finished = False
        self.writer = None
        self.buffer = ''

    def write(self, data):
        if self.headers_finished:
            self.response.write(data)
            return
        self.buffer += data
        while '\n' in self.buffer:
            if '\r\n' in self.buffer and self.buffer.find('\r\n') < self.buffer.find('\n'):
                line1, self.buffer = self.buffer.split('\r\n', 1)
            else:
                line1, self.buffer = self.buffer.split('\n', 1)
            if not line1:
                self.headers_finished = True
                self.response=HttpResponse(status=int(self.status.split(' ')[0]))
                for name, value in self.headers:
                    self.response[name]=value
                self.response.write(self.buffer)
                del self.buffer
                del self.headers
                del self.status
                break
            elif ':' not in line1:
                raise CGIError(
                    "Bad header line: %r" % line1)
            else:
                name, value = line1.split(':', 1)
                value = value.lstrip()
                name = name.strip()
                if name.lower() == 'status':
                    if ' ' not in value:
                        # WSGI requires this space, sometimes CGI scripts don't set it:
                        value = '%s General' % value
                    self.status = value
                else:
                    self.headers.append((name, value))
        
