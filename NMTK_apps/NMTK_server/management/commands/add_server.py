from django.core.management.base import BaseCommand, CommandError
from NMTK_server import models
from optparse import make_option
import datetime

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
                )
    def handle(self, *args, **options):
        if not len(args):
            raise CommandError('Please the name of the tool to add')
        if not options['url']:
            raise CommandError('Please provide the --url option and a server URL')
        m=models.ToolServer(name=args[0],
                            server_url=options['url'],
                            remote_ip=options['ip'])
        m.save()
        print "Tool information has been saved with an tool id (public key) of %s" % (m.pk,)
        print "Tool has a auth_key (private key) of '%s' (not including the surrounding single quotes.)" % (m.auth_token,)
        print "Please provide the tool id and auth_key to the maintainers of %s" % (m.name,)
