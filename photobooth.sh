#!/bin/bash

PHOTOBOOTH_DIR=/home/pi/photobooth

cd "${PHOTOBOOTH_DIR}"

sudo ./photobooth.py > photobooth.log 2> photobooth.err

cd -

