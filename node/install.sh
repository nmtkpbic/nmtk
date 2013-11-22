#!/bin/bash
FILE_PATH="$(dirname $0)"
FAIL=0
NODE_URL=http://nodejs.org/dist/v0.10.22/node-v0.10.22.tar.gz
if [[ ${FILE_PATH} > 0 ]]; then
   pushd $(dirname $0) >> /dev/null
fi
NODE_PREFIX=$(pwd)
if [[ ! -f $(basename $NODE_URL) ]]; then
  wget ${NODE_URL}
  if [[ $? != 0 ]]; then
    echo "Failed to download node source from ${NODE_URL}"
    FAIL=1
  fi
fi
if [[ $FAIL == 0 ]]; then
   tar xf $(basename $NODE_URL)
   pushd node* >> /dev/null
   NODE_DIR=$(pwd)
   ./configure --prefix=$NODE_PREFIX && make && make install
   popd
   bin/npm install -g requirejs
   bin/npm install -g uglify-js
fi

if [[ ${FILE_PATH} > 0 ]]; then
  popd >> /dev/null
fi
