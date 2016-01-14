#!/bin/bash
# Chander Ganesan
# Jan 2015
#
# NMTK Deployment script - used after a pull to deploy/update various things.
#  - Also useful after updating code (in test/dev) to get things updated.

DIRNAME=$(dirname $0)
push $DIRNAME &> /dev/null

CLEAN=0

usage () {
  # Simple function to output usage info...
  cat <<-EOF
  usage: $0 options
  
  This script is used after a git pull to deploy/refresh the code
  running NMTK.  Additionally, it may be used after a tool update/refresh
  to propagate various changes.  It is designed to be non-destructive when
  it comes to data.
  
  OPTIONS:
  
  -h   show this message (help)
  
EOF
}

yesno () {
  if [[ $1 == '0' ]]; then
    echo "No"
  else
    echo "Yes"
  fi
}

if [ -d venv/bin ]; then
  source venv/bin/activate
elif [ -d venv/scripts ]; then
  source venv/scripts/activate
fi

if [ -f .nmtk_config ]; then
  source .nmtk_config
fi

if [ ${#NMTK_NAME} == 0 ]; then
  NMTK_NAME=$(echo $HOSTN|cut -f1 -d.)
fi

echo "Gathering NMTK confguration details"
pushd NMTK_apps &> /dev/null
DB_TYPE=$(python manage.py query_settings -t)
echo "Database type is $DB_TYPE"
DB_NAME=$(python manage.py query_settings -d)
echo "Database name for this installation is $DB_NAME"
DB_USER=$(python manage.py query_settings -u)
echo "Database user is $DB_USER"
SELF_SIGNED_CERT=$(python manage.py query_settings --self-signed-cert)
echo "Using Self-Signed SSL Certificate? $(yesno $SELF_SIGNED_CERT)"
SERVER_ENABLED=$(python manage.py query_settings --nmtk-server-status)
echo "NMTK Server Enabled? $(yesno $SERVER_ENABLED)" 
TOOLSERVER_ENABLED=$(python manage.py query_settings --tool-server-status)
echo "Local Tool Server enabled? $(yesno $TOOLSERVER_ENABLED)" 
PRODUCTION=$(python manage.py query_settings --production)
echo "Minification required (production mode)? $(yesno $PRODUCTION)" 
TOOL_SERVER_URL=$(python manage.py query_settings --tool-server-url)

echo "Applying any outstanding database migrations..."
python manage.py migrate --noinput
echo "Restarting services..."
sudo service apache2 restart
sudo service celeryd-${NMTK_NAME} restart

python manage.py cleanup_mapfiles
if [[ ${SERVER_ENABLED} == 1 ]]; then
  echo "NMTK Server is enabled"
  echo "Rediscovering tools from tool servers..."
    python manage.py discover_tools
  echo "Tool discovery has been initiated, note that this may take some time to complete"
  if [[ $PRODUCTION == 1 ]]; then
    echo "Minifying code"
    python manage.py minify
  fi
  echo "Regenerating images for color ramps"
  python manage.py refresh_colorramps
fi
popd &> /dev/null
popd &> /dev/null
