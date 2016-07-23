#!/bin/bash

PHOTOBOOTH_DIR=/home/pi/photobooth

cd "${PHOTOBOOTH_DIR}"

if [[ $1 == "set-time" ]]; then
  sudo gnome-control-center datetime
fi

sudo python photobooth.py >>photobooth.log 2>>photobooth.err

cd -

