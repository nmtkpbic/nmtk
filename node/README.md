This directory is used for the installation of node.js and the required components for code minification/uglification.

The NTMK system uses require.js for combining files/templates into packages, then uses uglify to minify the code.  This
is a fairly straightfoward process.  Note that install.sh downloads and installs the required components.

Once installed, the "python manage.py minify" command takes care of minifying the code by using the software installed
here.

For obvious reasons, only an install script (and this README) are stored in git - the rest is installed on demand.
