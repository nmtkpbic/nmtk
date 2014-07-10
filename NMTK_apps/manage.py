#!/usr/bin/env python
import os
import sys

# Set up the virtualenv components.
import site
dir=os.path.dirname(__file__)
if dir:
    os.chdir(dir)
venv_dir='../venv/lib/python2.7/site-packages'

prev_sys_path=sys.path[:]
site.addsitedir(venv_dir)
sys.path[:0] = [sys.path.pop(pos) for pos, p in enumerate(sys.path) 
                if p not in prev_sys_path]


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "NMTK_apps.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
