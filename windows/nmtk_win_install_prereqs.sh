#!/bin/bash
pushd $(dirname $0)
echo "Renaming C:\\python27\\dlls\sqlite3.dll to C:\\python27\\dlls\\sqlite3.dll.old"
if [[ -f /c/python27/dlls/sqlite3.dll ]]; then
  mv /c/python27/dlls/sqlite3.dll /c/python27/dlls/sqlite3.dll.old
fi
WIN_DIR=$(pwd)
cd ..
mkdir tmp
pushd tmp
curl http://python-distribute.org/distribute_setup.py > distribute_setup.py
curl https://raw.githubusercontent.com/pypa/pip/1.5.X/contrib/get-pip.py > get-pip.py
python distribute_setup.py
python get-pip.py
pip install virtualenv
popd
virtualenv venv
source venv/Scripts/activate
pip install -r ${WIN_DIR}/win-requirements.txt
mkdir packages
pushd packages
start .
URLS="https://pypi.python.org/pypi/lxml/3.2.3#downloads http://www.stickpeople.com/projects/python/win-psycopg/ http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal http://matplotlib.org/downloads.html"
echo "Please download the packages from the following URLS into the open 'packages' window"
for URL in $URLS; do
  echo $URL
  start $URL
done
echo "Press enter once your downloads are complete, and moved to the directory"
read
for FILE in *.exe; do
   easy_install "$FILE"
done
popd
GDAL_PATH=$(echo "$(pwd)/$(dirname $(find venv -name gdal111.dll))"|sed -e 's/\///' -e 's/\//\\/g' -e 's/\\/:\\/')
VENV_PATH="\$PATH:/c/python27/dlls:/c/python27/scripts:$(pwd)/$(dirname $(find venv -name gdal111.dll)):/c/osgeo4w/bin:"
echo "PATH=$VENV_PATH" >> venv/scripts/activate
echo "export PATH" >> venv/scripts/activate
popd
