from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from django.conf import settings
import os
import subprocess

class Command(BaseCommand):
    help = 'Minify existing JavaScript code and produce nmtk_ui_app.min.js'
    option_list = BaseCommand.option_list + (
                    make_option('-n','--no-optimize',
                        action='store_true',
                        dest='nooptimize',
                        default=False,
                        help='Tell r.js to not minify the code.'),)
    def handle(self, *args, **options):
        # Find node
        node_path=getattr(settings,'NODE_PATH')
        if not os.path.exists(node_path):
            raise CommandError('Node is not installed, minifcation is not possible (check settings.py - is NODE_PATH valid?)')
        environ=os.environ.copy()
        environ['PATH']='{0}:{1}'.format(os.environ['PATH'], node_path)
        rjs = os.path.join(node_path,'r.js')
        js_dir=os.path.join(settings.BASE_PATH,'..','NMTK_ui','static','NMTK_ui','js')
        # check to see if optimize has been turned off.
        optimize=[]
        if (options['nooptimize']):
            optimize=['optmize=none',]
        os.chdir(js_dir)
        # call r.js
        subprocess.call([rjs, '-o', 'nmtk_ui.profile.js'] + optimize,
             env=environ)
