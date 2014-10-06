from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from django.conf import settings
class Command(BaseCommand):
    help = 'List the database type.'
    option_list = BaseCommand.option_list + (
                make_option('-t','--type',
                    action='store_true',
                    dest='type',
                    default=False,
                    help='Print the database type.'), 
                make_option('-d','--database',
                    action='store_true',
                    dest='database',
                    default=False,
                    help='Provide the name of the database.'),                         
                make_option('-u','--username',
                    action='store_true',
                    dest='username',
                    default=False,
                    help='Provide the name of the database user.'),                         
                )
    def handle(self, *args, **options):
        if options['type']:
            print getattr(settings,'DATABASE_TYPE')
        elif options['database']:
            print settings.DATABASES['default']['NAME']
        elif options['username']:
            print settings.DATABASES['default']['USER']