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
# Script to install/reset the NMTK environment for testing.
cat <<-EOT
	NOTICE: This script will cause the removal of all data, accounts, etc. 
	        stored on this server.  For a new installation, it is acceptable
	        to run this script once to set things up, but unless you 
	        are running a development/test server and are trying to reset it, 
	        you should answer "N" to the question below.
EOT
if [[ "${OS}" == "Windows_NT" ]]; then
  echo "This script does not work on Windows platforms"
  exit 1
else
  WINDOWS=0
fi
echo -n "Reset Server (remove all data) y/N? "
read ANSWER
if [[ "${ANSWER}" != 'Y' && "${ANSWER}" != 'y' ]]; then
  echo "Cancelling execution"
  exit 1
fi
pushd $(dirname $0) &>/dev/null
NMTK_INSTALL_PATH=$(pwd)
for DIR in nmtk_files logs htdocs/static; do
  if [[ ! -d $DIR ]]; then
    mkdir -p $DIR
  fi
  if [[ $WINDOWS == 0 ]]; then
    sudo chown -R $USER.www-data $DIR
    sudo find $DIR -type d -exec chmod -R g+rwxs {} \;
    sudo find $DIR -exec chmod -R g+rw {} \;
  fi
done
if [ -f ./.nmtk_config ]; then
  source ./.nmtk_config
fi
if [ ${#HOSTN} == 0 ]; then
  read -p "URL Hostname (press enter for ${HOSTN:=$HOSTNAME}): " HOSTN 
  if [[ ${#HOSTN} == 0 ]]; then
    HOSTN=$HOSTNAME
  fi
fi
if [ ${#SSL} == 0 ]; then
  echo -n "Use SSL (Y/n)?  "
  read ANSWER
  if [[ "${ANSWER}" != 'Y' && "${ANSWER}" != 'y' ]]; then
    SSL=0
  else
    SSL=1
  fi
fi
HTTP='http'
if [[ ${SSL} != 0 ]]; then
  HTTP='https'
fi
if [[ $WINDOWS == 0 ]] ; then
  if [ ${#NMTK_NAME} == 0 ]; then
    #NMTK_NAME=$(hostname -s)
    NMTK_NAME=$(echo $HOSTN|cut -f1 -d.)
  fi
  if [ ${#URL} == 0 ]; then
    #echo -n "Enter URL for this tool server (Enter for http(s)://${HOSTN}/): "
    #read URL
    if [ ${#URL} == 0 ]; then
      URL="$HTTP://${HOSTN}/"
    fi
  fi
else
  echo "Windows uses http://127.0.0.1:8000"
  URL="http://127.0.0.1:8000"
fi
if [ ${#NMTK_USERNAME} == 0 ]; then
  echo -n "NMTK Username: " 
  read NMTK_USERNAME
fi
if [ ${#EMAIL} == 0 ]; then
  echo -n "Email Address: "
  read EMAIL
fi
CONF_FILE='apache.conf'
if [[ ${SSL} != 0 ]]; then
  CONF_FILE='apache-ssl.conf'
fi
echo "Using configuration file for apache in conf/$CONF_FILE"
if [ ${#PASSWORD} == 0 ]; then
  echo -n "Enter Password for user $NMTK_USERNAME (to access the NMTK ui): "
  read -s PASSWORD
  echo
fi
if [ ${#FIRSTNAME} == 0 ]; then
  echo -n "First Name: "
  read FIRSTNAME
fi
if [ ${#LASTNAME} == 0 ]; then
  echo -n "Last Name: "
  read LASTNAME
fi
if [ ${#PGUSER} == 0 ]; then
  read -p "PostgreSQL Username (press enter for ${USER:=$USERNAME}): " PGUSER 
  if [[ ${#PGUSER} == 0 ]]; then
    PGUSER=$USER
  fi
fi

if [ ${#PGPASSWORD} == 0 ]; then
  read -s -p "PostgreSQL Password for $PGUSER (will not echo): " PGPASSWORD
  echo ""
fi
export FIRSTNAME LASTNAME PASSWORD EMAIL NMTK_USERNAME NMTK_NAME URL PGUSER PGPASSWORD SSL CONF_FILE HOSTN
   cat <<-EOT > .nmtk_config
	# These settings were built from the first run of the install.sh script
	# to change them, remove this file and re-run the install script.
	# it is advisable not to change the NMTK_NAME, as doing so might
	# result in duplicate config/startup scripts.
	NMTK_USERNAME=$NMTK_USERNAME
	EMAIL=$EMAIL
	FIRSTNAME=$FIRSTNAME
	LASTNAME=$LASTNAME
	NMTK_NAME=${NMTK_NAME}
	URL=${URL}
	PGUSER=${PGUSER}
	SSL=${SSL}
	HOSTN=${HOSTN}
EOT

if [[ $WINDOWS == 0 ]]; then
sudo -s -- <<EOF
# Install the celery startup scripts
#if [ ! -f "/etc/default/celeryd-${NMTK_NAME}" ]; then
  sed -e 's|NMTK_INSTALL_PATH|'${NMTK_INSTALL_PATH}'|g' \
      -e 's|NMTK_NAME|'${NMTK_NAME}'|g' \
    celery/celeryd-nmtk.default > /etc/default/celeryd-${NMTK_NAME}
  sed -e 's|NMTK_INSTALL_PATH|'${NMTK_INSTALL_PATH}'|g' \
      -e 's|NMTK_NAME|'${NMTK_NAME}'|g' \
    celery/celeryd-nmtk.init > /etc/init.d/celeryd-${NMTK_NAME}
  chmod +x /etc/init.d/celeryd-${NMTK_NAME}
  update-rc.d celeryd-${NMTK_NAME} defaults 
#fi

#if [ ! -f "/etc/apache2/sites-available/${NMTK_NAME}.conf" ]; then
  sed -e 's|NMTK_INSTALL_PATH|'${NMTK_INSTALL_PATH}'|g' \
    -e 's|EMAIL|'${EMAIL}'|g' \
    -e 's|HOSTNAME|'${HOSTN}'|g' \
    -e 's|NMTK_NAME|'${NMTK_NAME}'|g' \
    conf/${CONF_FILE} > /etc/apache2/sites-available/${NMTK_NAME}.conf
  a2ensite ${NMTK_NAME}.conf
#fi
EOF
echo ${NMTK_NAME}.conf

BASEDIR=$(dirname $0)
CELERYD_NAME=${NMTK_NAME}
echo -n "Stopping the celery daemon (this might take a few seconds)."
if [[ -f /var/run/celery/$CELERYD_NAME.pid ]]; then
   sudo kill $(cat /var/run/celery/$CELERYD_NAME.pid)
   sleep 15
   echo -n "."
   if [[ -f /var/run/celery/$CELERYD_NAME.pid ]]; then
      echo "Unable to stop celery daemon!"
      exit 1
   fi
fi
else
  BASEDIR=$(dirname $0)
fi
echo ""
pushd $BASEDIR &> /dev/null
BASEDIR=$(pwd)
if [[ $WINDOWS == 0 ]]; then
  sudo rm -rf nmtk_files/*
  source venv/bin/activate
else
  rm -rf nmtk_files/*
  source venv/scripts/activate
fi

pushd NMTK_apps &> /dev/null
DB_TYPE=$(python manage.py query_settings -t)
DB_NAME=$(python manage.py query_settings -d)
DB_USER=$(python manage.py query_settings -u)
SELF_SIGNED_CERT=$(python manage.py query_settings --self-signed-cert)
SERVER_ENABLED=$(python manage.py query_settings --nmtk-server-status)
TOOLSERVER_ENABLED=$(python manage.py query_settings --tool-server-status)
PRODUCTION=$(python manage.py query_settings --production)
TOOL_SERVER_URL=$(python manage.py query_settings --tool-server-url)
pushd ../nmtk_files &> /dev/null

  echo "Removing existing database (if it exists)"
  dropdb $DB_NAME
  echo "Creating new database $DB_NAME"
  createdb $DB_NAME -O $DB_USER
  echo "Installing PostGIS in database $DB_NAME"
  psql -U $PGUSER $DB_NAME -c "create extension postgis;"

popd &> /dev/null
python manage.py syncdb --noinput
# Use the -l argument for development, otherwise js/css changes require recopying

if [[ $PRODUCTION == 1 && ! -f "$BASEDIR/node/bin/npm" ]]; then
  $BASEDIR/node/install.sh
fi

if [[ ${SERVER_ENABLED} == 1 ]]; then
  echo "NMTK Server is enabled, setting up default account, etc."
  python manage.py createsuperuser --noinput --email=$EMAIL --username=$NMTK_USERNAME
  echo "from django.contrib.auth import get_user_model; User=get_user_model(); u = User.objects.get(username__exact='$NMTK_USERNAME'); u.set_password('$PASSWORD'); u.first_name='$FIRSTNAME'; u.last_name='$LASTNAME'; u.save()"|python manage.py shell
#  echo "from NMTK_server.models import ToolServer; m = ToolServer.objects.all()[0]; m.server_url='${URL}'; m.save()"|python manage.py shell
  python manage.py discover_tools
  echo "Tool discovery has been initiated, note that this may take some time to complete"
  if [[ $PRODUCTION == 1 ]]; then
    python manage.py minify
  fi
  echo "Regenerating images for color ramps"
  python manage.py refresh_colorramps
fi



python manage.py collectstatic --noinput -l -c
deactivate
popd &> /dev/null
if [[ $WINDOWS == 0 ]]; then
  for DIR in nmtk_files logs; do
    sudo chown -R www-data.$USER $DIR
    sudo find $DIR -type d -exec chmod -R g+rwxs {} \;
    sudo find $DIR -exec chmod -R g+rw {} \;
  done
fi
if [[ ${SERVER_ENABLED} == 1 && ${TOOLSERVER_ENABLED} == 1 ]]; then
  if [[ ${SELF_SIGNED_CERT} == 1 ]]; then
    ADDITIONAL_ARGS="--self-signed-ssl"
  fi
fi
if [[ $WINDOWS == 0 ]]; then
  sudo a2dissite 000-default.conf &> /dev/null
  sudo /etc/init.d/apache2 restart
  sudo /etc/init.d/celeryd-$CELERYD_NAME start
  
  echo "Adding the local tool server to the NMTK server [Note: this may take some time as the celery queue may be full]"
  $BASEDIR/venv/bin/python $BASEDIR/NMTK_apps/manage.py add_server $ADDITIONAL_ARGS -c $EMAIL -U $NMTK_USERNAME -u $TOOL_SERVER_URL "Local Sample Tool Server"|$BASEDIR/venv/bin/python $BASEDIR/NMTK_apps/manage.py add_nmtk_server
else
  echo "To start the Windows development server run the commands:  "
  echo "start python NMTK_apps/manage.py celeryd"
  echo "start python NMTK_apps/manage.py runserver"
  echo "$BASEDIR/venv/bin/python $BASEDIR/NMTK_apps/manage.py add_server $ADDITIONAL_ARGS -c $EMAIL -U $NMTK_USERNAME -u $TOOL_SERVER_URL "Local Sample Tool Server"|$BASEDIR/venv/bin/python $BASEDIR/manage.py add_nmtk_server"
  
fi
popd &> /dev/null
popd &> /dev/null

