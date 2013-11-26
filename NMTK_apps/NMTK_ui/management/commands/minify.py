from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from django.conf import settings
import os
import subprocess

class Command(BaseCommand):
    help = 'Minify existing JavaScript code and produce nmtk_ui_app.min.js'
    option_list = BaseCommand.option_list + (
                    make_option('-o','--optimize',
                        action='store_true',
                        dest='optimize',
                        default=False,
                        help='Tell r.js to uglify the code.'),)
    def handle(self, *args, **options):
        # Find node
        node_path=getattr(settings,'NODE_PATH')
        if not os.path.exists(node_path):
            raise CommandError('Node is not installed, minifcation is not possible (check settings.py - is NODE_PATH valid?)')
        environ=os.environ.copy()
        environ['PATH']='{0}:{1}'.format(os.environ['PATH'], node_path)
        rjs = os.path.join(node_path,'r.js')
        js_dir=os.path.abspath(os.path.join(settings.BASE_PATH,
                                            '..','NMTK_ui',
                                            'static','NMTK_ui',
                                            'js'))
        # check to see if optimize has been turned off.
        optimize=[]
        if (not options['optimize']):
            optimize=['optimize=none',]
        os.chdir(js_dir)
        # call r.js
        subprocess.call([rjs, '-o', 'nmtk_ui.profile.js'] + optimize,
             env=environ)
        combined=os.path.join(js_dir, 'nmtk_ui_app.combined.js')
        print "Combined JavaScript is at {0}".format(combined)
        output=os.path.join(js_dir, 'nmtk_ui_app.min.js')
        uglify=os.path.join(node_path,'uglifyjs')
        subprocess.call([uglify, combined,'-o', output],
                        env=environ)
        print "Minified JavaScript is at {0}".format(output)