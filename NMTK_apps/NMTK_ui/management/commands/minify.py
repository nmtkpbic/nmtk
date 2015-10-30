#!/usr/bin/env python
# Nonmotorized Toolkit
# Copyright (c) 2014 Open Technology Group Inc. (A North Carolina Corporation)
# Developed under Federal Highway Administration (FHWA) Contracts:
# DTFH61-12-P-00147 and DTFH61-14-P-00108
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer
#       in the documentation and/or other materials provided with the distribution.
#     * Neither the name of the Open Technology Group, the name of the
#       Federal Highway Administration (FHWA), nor the names of any
#       other contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# Open Technology Group Inc BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
# USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from django.conf import settings
import os
import subprocess


class Command(BaseCommand):
    help = 'Minify existing JavaScript code and produce nmtk_ui_app.min.js'
    option_list = BaseCommand.option_list + (
        make_option('-o', '--optimize',
                    action='store_true',
                    dest='optimize',
                    default=False,
                    help='Tell r.js to uglify the code.'),)

    def handle(self, *args, **options):
        # Find node
        node_path = getattr(settings, 'NODE_PATH')
        if not os.path.exists(node_path):
            raise CommandError(
                'Node is not installed, minifcation is not possible (check settings.py - is NODE_PATH valid?)')
        environ = os.environ.copy()
        environ['PATH'] = '{0}:{1}'.format(os.environ['PATH'], node_path)
        rjs = os.path.join(node_path, 'r.js')
        js_dir = os.path.abspath(os.path.join(settings.BASE_PATH,
                                              '..', 'NMTK_ui',
                                              'static', 'NMTK_ui',
                                              'js'))
        # check to see if optimize has been turned off.
        optimize = []
        if (not options['optimize']):
            optimize = ['optimize=none', ]
        os.chdir(js_dir)
        # call r.js
        subprocess.call([rjs, '-o', 'nmtk_ui.profile.js'] + optimize,
                        env=environ)
        combined = os.path.join(js_dir, 'nmtk_ui_app.combined.js')
        print "Combined JavaScript is at {0}".format(combined)
        output = os.path.join(js_dir, 'nmtk_ui_app.min.js')
        uglify = os.path.join(node_path, 'uglifyjs')
        subprocess.call([uglify, combined, '-o', output],
                        env=environ)
        print "Minified JavaScript is at {0}".format(output)
