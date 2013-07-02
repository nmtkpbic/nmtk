from django.core.management.base import BaseCommand, CommandError
from NMTK_server import models
from optparse import make_option
import datetime
from NMTK_server import tasks


class Command(BaseCommand):
    help = 'Go out to the NMTK servers and discover new tools, update configs.'
    option_list = BaseCommand.option_list + (
                make_option('-t','--tool-name',
                    type='string',
                    action='store',
                    dest='tool_name',
                    default=None,
                    help='Specify a single tool server ID to update.'),             
                )
    def handle(self, *args, **options):
        '''
        A save of the toolserver model will trigger an update of the config
        for that toolserver.
        '''
        qs=models.ToolServer.objects.all()
        for m in qs:
            self.stdout.write('Updating ToolServer record for %s' % m.name)
#            m.save()
            tasks.discover_tools.delay(m)

