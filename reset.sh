#!/bin/bash
# Non-Motorized Toolkit
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
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# Chander's script to reset his NMTK environment for testing.
# First stop celery
pushd $(dirname $0)
if [ -f ./config ]; then
  source ./config
fi
if [ ${#USERNAME} == 0 ]; then
  echo -n "Username: " 
  read USERNAME
fi
if [ ${#EMAIL} == 0 ]; then
  echo -n "Email Address: "
  read EMAIL
fi
if [ ${#PASSWORD} == 0 ]; then
  echo -n "Password: "
  read -s PASSWORD
fi
if [ ${#FIRSTNAME} == 0 ]; then
  echo -n "Password: "
  read -s FIRSTNAME
fi
if [ ${#LASTNAME} == 0 ]; then
  echo -n "Password: "
  read -s LASTNAME
fi
export FIRSTNAME LASTNAME PASSWORD EMAIL USERNAME

BASEDIR=$(dirname $0)
CELERYD_NAME=$(hostname -s)
if [[ -f /var/run/celery/$CELERYD_NAME.pid ]]; then
   sudo kill $(cat /var/run/celery/$CELERYD_NAME.pid)
   sleep 15
   if [[ -f /var/run/celery/$CELERYD_NAME.pid ]]; then
      echo "Unable to stop celery daemon!"
      exit 1
   fi
fi

pushd $BASEDIR
sudo rm -rf nmtk_files/*
source venv/bin/activate
pushd NMTK_apps
pushd ../nmtk_files
spatialite nmtk.sqlite  "SELECT InitSpatialMetaData();"
popd
python manage.py syncdb --noinput
# Use the -l argument for development, otherwise js/css changes require recopying
python manage.py collectstatic --noinput -l -c
python manage.py createsuperuser --noinput --email=$EMAIL --username=$USERNAME
echo "from django.contrib.auth.models import User; u = User.objects.get(username__exact='$USERNAME'); u.set_password('$PASSWORD'); u.first_name='$FIRSTNAME'; u.last_name='$LASTNAME'; u.save()"|python manage.py shell
python manage.py discover_tools
deactivate
popd
sudo chown -R www-data nmtk_files/*
sudo chmod g+rw nmtk_files/*
popd

sudo /etc/init.d/apache2 restart
sudo /etc/init.d/celeryd-$CELERYD_NAME start
popd


