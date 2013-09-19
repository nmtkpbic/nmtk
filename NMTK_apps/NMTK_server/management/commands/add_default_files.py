from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from NMTK_server.default_data.init_account import setupAccount

class Command(BaseCommand):
    help = 'Add default files to user accounts '
           '(all accounts, or specify space-separate names on the command line).'
    def handle(self, *args, **options):
        if args:
            qs = User.objects.filter(username__in=args)
        else:
            qs = User.objects.all()

        if qs.exists():
            for user in qs:
                if user.datafile_set.count() == 0:
                    print "Setting up default files for user '%s'"%(user.username,)
                    setupAccount(user)
                else:
                    print "User '%s' already has files."%(user.username,)
        else:
            print "No users found!"
