#!/bin/bash
# Chander Ganesan <chander@otg-nc.com>
# Script to build ng-Bootstrap for NMTK.  The path should be edited before running this
# so that it points to the correct node installation.
#
# We use a pre-release of ng-bootstrap on the bootstrap3 branch, so it needs to be
# built specifically for us (since there is no distributed version.)
export PATH=/var/www/vhosts/nmtk-dev.otg-nc.com/node/bin/:$PATH
if [ -d bs ]; then
   rm -rf bs
fi
git clone https://github.com/angular-ui/bootstrap.git bs
cd bs
git checkout bootstrap3
npm install -g grunt-cli
npm install
grunt --force
ls dist/ui-bootstrap-tpls-0.7.0.js
