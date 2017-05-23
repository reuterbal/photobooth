#!/bin/bash

cd $(dirname $0)	# Directory of this script

if [[ $1 == "set-time" ]]; then
  sudo python set-time.py
fi

if v4l2-ctl --silent 2>/dev/null; then
    # If camera uses JPEG compression, improve the quality  
    v4l2-ctl -c compression_quality=100 2>/dev/null
fi    

sudo python photobooth.py >>photobooth.log 2>>photobooth.err


