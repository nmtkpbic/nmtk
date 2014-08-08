from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import datetime
from NMTK_server import tasks
from django.conf import settings
class Command(BaseCommand):
    help = 'Add a new tool server for use by the NMTK API.'
    option_list = BaseCommand.option_list + (
                make_option('-i','--ip-restrict',
                    type='string',
                    action='store',
                    dest='ip',
                    default=None,
                    help='Provide the remote IP for the tool.'), 
                make_option('-u','--url',
                    type='string',
                    action='store',
                    dest='url',
                    default=None,
                    help='Provide the base URL for the tool server.'),             
                make_option('-U','--username',
                    type='string',
                    action='store',
                    dest='username',
                    default=None,
                    help='Provide the username for the user that is adding the server.'),             
                )
    def handle(self, *args, **options):
        if not settings.NMTK_SERVER:
            raise CommandError('The NMTK Server is not currently enabled')
        if not len(args):
            raise CommandError('Please the name of the tool to add')
        if not options['url']:
            raise CommandError('Please provide the --url option and a server URL')
        if not options['username']:
            raise CommandError('Please provide the --username option and a username')
#        try:
#            user=User.objects.get(username=options['username'])
#        except Exception, e:
#            raise CommandError('Username specified (%s) not found!' % 
#                               options['username'])
        task=tasks.add_toolserver.delay(name=args[0],
                                        url=options['url'],
                                        remote_ip=options['ip'],
                                        username=options['username'])
        m=task.get()
        print "Tool information has been saved with an tool id (public key) of %s" % (m.pk,)
        print "Tool has a auth_key (private key) of '%s' (not including the surrounding single quotes.)" % (m.auth_token,)
        print "Please provide the tool id and auth_key to the maintainers of %s" % (m.name,)
