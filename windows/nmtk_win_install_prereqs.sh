#!/bin/bash
pushd $(dirname $0)
WIN_DIR=$(pwd)
cd ..
pushd /c/python2*/dlls/
mv sqlite.dll sqlite.dll.old
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
URLS="https://pypi.python.org/pypi/lxml/3.2.3#downloads http://www.stickpeople.com/projects/python/win-psycopg/ http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal"
echo "Please download the packages from the following URLS into the open 'packages' window"
for URL in $URLS; do
  echo $URL
  start $URL
done
echo "Press enter once your downloads are complete, and moved to the directory"
read
for FILE in *.exe; do
   easy_install $FILE
done
echo "Please rename the sqlite.dll file in your Python installation to sqlite.dll.old"
echo "Please add the path '$(find venv -name gdal111.dll|dirname)' to the end of your Windows PATH, then close this window and open a new one"
popd
popd