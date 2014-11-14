from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from NMTK_server import models
from NMTK_server.wms import legend

from django.conf import settings
class Command(BaseCommand):
    help = 'Populate the color ramp images.'
    def handle(self, *args, **options):
        ramps=dict((m.matplotlib_name, m) for m in models.MapColorStyle.objects.all())
        formats=legend.LegendGenerator.supported_formats()
        i=0
        for category, styles in formats:
            for style in styles:
                m=ramps.get(style, models.MapColorStyle())
                m.matplotlib_name=style
                m.description='Color ramp well suited for {0} data'.format(category.lower())
                m.other_r=20
                m.other_g=20
                m.other_b=20
                m.default=(style == 'hsv')
                m.save()
                i += 1
        print "Regenerated images for {0} Map Color Styles".format(i)