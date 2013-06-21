from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Purge an existing user from the database.'
    def handle(self, *args, **options):        
        for user in args:
            User.objects.filter(username=user).delete()
