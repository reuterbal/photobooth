#!/bin/bash

PHOTOBOOTH_DIR=/home/pi/photobooth

cd "${PHOTOBOOTH_DIR}"

sudo ./photobooth.py 2>&1 > photobooth.log

