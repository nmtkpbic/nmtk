from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from django.conf import settings
from django.core.urlresolvers import reverse


class Command(BaseCommand):
    help = 'List the database type.'
    option_list = BaseCommand.option_list + (
        make_option('-t', '--type',
                    action='store_true',
                    dest='type',
                    default=False,
                    help='Print the database type.'),
        make_option('-d', '--database',
                    action='store_true',
                    dest='database',
                    default=False,
                    help='Provide the name of the database.'),
        make_option('-u', '--username',
                    action='store_true',
                    dest='username',
                    default=False,
                    help='Provide the name of the database user.'),
        make_option('--self-signed-cert',
                    action='store_true',
                    dest='self_signed_cert',
                    default=False,
                    help='Return a 1 if the server is using a self signed certificate, 0 otherwise..'),
        make_option('--nmtk-server-status',
                    action='store_true',
                    dest='nmtk_server_status',
                    default=False,
                    help='Return a 1 if the NMTK Server is enabled, 0 otherwise..'),
        make_option('--tool-server-status',
                    action='store_true',
                    dest='tool_server_status',
                    default=False,
                    help='Return a 1 if the Tool Server is enabled, 0 otherwise..'),
        make_option('--production',
                    action='store_true',
                    dest='production',
                    default=False,
                    help='Return a 1 if the NMTK server is in production (minified UI).'),
        make_option('--tool-server-url',
                    action='store_true',
                    dest='tool_server_url',
                    default=False,
                    help='Return the URL for the Tool server.'),
    )

    def handle(self, *args, **options):
        if options['type']:
            print getattr(settings, 'DATABASE_TYPE')
        elif options['database']:
            print settings.DATABASES['default']['NAME']
        elif options['username']:
            print settings.DATABASES['default']['USER']
        elif options['self_signed_cert']:
            if getattr(settings, 'SELF_SIGNED_SSL_CERT', 1):
                print 1
            else:
                print 0
        elif options['nmtk_server_status']:
            if settings.NMTK_SERVER:
                print 1
            else:
                print 0
        elif options['tool_server_status']:
            if settings.TOOL_SERVER:
                print 1
            else:
                print 0
        elif options['production']:
            if settings.PRODUCTION:
                print 1
            else:
                print 0
        elif options['tool_server_url']:
            if getattr(settings, 'SSL', True):
                ssl = 's'
            else:
                ssl = ''
            print 'http{0}://{1}{2}{3}'.format(ssl,
                                               settings.SITE_DOMAIN,
                                               getattr(settings, 'PORT', ''),
                                               reverse('tool_index'))
