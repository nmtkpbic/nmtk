from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import datetime
from NMTK_tools import tasks
from django.conf import settings
import json
import sys


class Command(BaseCommand):
    help = 'Add a new tool server for use by this tool server..'

    def handle(self, *args, **options):
        parameters = None
        if not settings.TOOL_SERVER:
            raise CommandError('The Tool Server is not currently enabled')
        if not len(args):
            if not args:
                parameters = json.load(sys.stdin)
            if not parameters:
                raise CommandError(
                    'Please the path to the file containing the NMTK Server configuration, or pass the data in via a pipe')
        if not parameters:
            with open(args[1]) as data_file:
                parameters = json.load(data_file)
        task = tasks.add_nmtkserver.delay(parameters=parameters)
        m = task.get()
        print "The NMTK Server information has been successfully imported"
