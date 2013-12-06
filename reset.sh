#!/bin/bash
# Chander's script to reset his NMTK environment for testing.
# First stop celery
USERNAME=chander
EMAIL=chander@otg-nc.com
PASSWORD=jraw123
FIRSTNAME="Chander"
LASTNAME="Ganesan"
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


