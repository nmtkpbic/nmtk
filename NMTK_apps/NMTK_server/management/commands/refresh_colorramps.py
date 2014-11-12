from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from NMTK_server import models

from django.conf import settings
class Command(BaseCommand):
    help = 'Refresh all the color ramp images.'
    def handle(self, *args, **options):
        i=[m.save() for m in models.MapColorStyle.objects.all()]
        print "Regenerated images for {0} Map Color Styles".format(len(i))