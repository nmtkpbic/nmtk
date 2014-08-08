from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.conf import settings

class Command(BaseCommand):
    help = 'Purge an existing user from the database.'
    def handle(self, *args, **options):  
        if not settings.NMTK_SERVER:
            raise CommandError('The NMTK Server is not currently enabled')      
        for user in args:
            User.objects.filter(username=user).delete()
