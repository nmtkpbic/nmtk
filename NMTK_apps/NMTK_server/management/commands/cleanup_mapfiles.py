from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from NMTK_server import tasks


class Command(BaseCommand):
    help = '''Remove existing mapfiles (they will get rebuilt when requests occur.)'''

    def handle(self, *args, **options):
        if not settings.NMTK_SERVER:
            raise CommandError('The NMTK Server is not currently enabled')

    result = tasks.cleanup_mapfiles.delay()
    print "Removing existing mapfiles..."
    task_output = result.get(timeout=600)
