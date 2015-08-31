from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import datetime
from NMTK_server import tasks
from django.conf import settings
from django.core.mail import send_mail, mail_admins
from django.template.loader import render_to_string
import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'A simple cron job to verify if the celery daemon is running and tasks can round-trip sucessfully.'
    option_list = BaseCommand.option_list + (
        make_option('--email-admins',
                    action='store_true',
                    dest='email_admins',
                    default=False,
                    help='Email the admins on error..'),
        make_option('--timeout',
                    type='int',
                    action='store',
                    dest='timeout',
                    default=600,
                    help='Specify how long to wait before considering the task failed (default is 600 seconds)'),
    )

    def handle(self, *args, **options):
        '''
        Check to see if we can run a celery task and get a suitable result back.
        '''
        if not settings.NMTK_SERVER:
            raise CommandError('The NMTK Server is not currently enabled')
        try:
            result = tasks.verify_celery.delay()
            task_output = result.get(timeout=options['timeout'])
        except Exception, e:
            task_output = False
        if task_output:
            exit(0)
        elif options['email_admins']:
            url = 'http{0}://{1}{2}'.format('s' if settings.SSL else '',
                                            settings.SITE_DOMAIN,
                                            settings.PORT)
            context = {'timeout': options['timeout'],
                       'url': url}
            subject = render_to_string('NMTK_server/verify_celery_subject.txt',
                                       context).strip().replace('\n', ' ')
            message = render_to_string('NMTK_server/verify_celery_message.txt',
                                       context)
            logger.debug(
                'Celery job validation failed, sending notification email to admins')
            mail_admins(subject, message)
            exit(1)
        else:
            raise CommandError(
                'The celery task has not returned after {0} seconds!'.format(options['timeout']))
