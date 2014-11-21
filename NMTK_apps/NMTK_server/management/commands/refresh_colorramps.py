from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from NMTK_server import models
from NMTK_server.wms import legend

from django.conf import settings
class Command(BaseCommand):
    help = 'Populate the color ramp images.'
    def handle(self, *args, **options):
        ramps=dict((m.name, m) for m in models.MapColorStyle.objects.all())
        formats=legend.LegendGenerator.supported_formats()
        i=0
        for category, styles in formats:
            for style in styles:
                m=ramps.get(style, models.MapColorStyle())
                m.name=style
                m.description='{0} color ramp style'.format(style)
                m.category=category
                # Only set this if we are populating from scratch
                if not m.pk:
                    m.other_g=m.other_b=m.other_r=0x94
                # Our default style is HSV.
                m.default=(style == 'hsv')
                m.save()
                i += 1
        print "Regenerated images for {0} Map Color Styles".format(i)