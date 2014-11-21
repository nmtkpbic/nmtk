from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from django.contrib.auth.models import User
from django.core import serializers


from django.conf import settings
class Command(BaseCommand):
    help = 'Return a fixture containing user accounts excluding the default disabled account.'
    def handle(self, *args, **options):
        qs=User.objects.exclude(username__iexact='disabled_user')
        data = serializers.serialize("json", qs)
        print data