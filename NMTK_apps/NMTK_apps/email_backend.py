'''
A class to cause the local sendmail daemon (or it's equivalent) to
be used (via the sendmail command) when sending email.  This assumes
that the local MTA is setup properly and working.
'''
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from subprocess import Popen,PIPE
import logging
logger=logging.getLogger(__name__)
class EmailBackend(BaseEmailBackend):
    '''
    Backend to handle local sending of email using the sendmail process.
    '''
    def __init__(self, fail_silently=False, **kwargs):
        super(EmailBackend, self).__init__(fail_silently=fail_silently)
        
    def open(self):
        return True
    
    def close(self):
        pass
    
    def send_messages(self, email_messages):
        """
        Sends one or more EmailMessage objects and returns the number of email
        messages sent.
        """
        if not email_messages:
            return
        num_sent = 0
        for message in email_messages:
            sent = self._send(message)
            if sent:
                num_sent += 1
        return num_sent
    
    def _send(self, email_message):
        """
        A helper method that does the actual sending.
        """
        if not email_message.recipients():
            return False
        try:
#            logger.debug('Sending email: %s',
#                         ["/usr/sbin/sendmail"]+list(email_message.recipients()))
            ps = Popen(["/usr/sbin/sendmail"]+list(email_message.recipients()), \
                       stdin=PIPE)
#            logger.debug('Writing message to pipe: %s',
#                         email_message.message().as_string())
            ps.stdin.write(email_message.message().as_string())
            ps.stdin.flush()
            ps.stdin.close()
            return not ps.wait()
        except:
            if not self.fail_silently:
                raise
            return False
        return True