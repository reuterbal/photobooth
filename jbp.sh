#!/bin/bash

# jbp.sh: Add jessie backports and install gphoto2

# The current raspian as of early 2017 (Debian Jessie) comes with
# a version of gphoto that is too old. However, it is easy to
# get a "backport" from Debian Stretch.

# This script will do all the steps for you.


# First a sanity check
v=$(cat /etc/debian_version)
if [ "${v%.*}" != "8" ]; then
    echo "Warning! This script was designed for Debian 8 (Jessie)."
    echo "You are running Debian version $v."
    echo -n "If you know what you're doing, type Y: "
    read -n 1
    echo
    if [ "$REPLY" != "Y" and "$REPLY" != "y" ]; then
	echo "Exiting"
	exit
    else
	echo "Continuing as you requested..."
    fi
fi




# Get the Debian Jessie archive signing key and trust it
keyid=7638D0442B90D010
gpg --recv-keys $keyid
gpg -a --export $keyid       | sudo apt-key add -

# Tell raspian to use the backports archive
sudo tee /etc/apt/sources.list.d/jessie-backports.list <<EOF
# Add in backports from Debian Jessie
# (This was automatically added by photobooth for gphoto2)
deb http://ftp.debian.org/debian jessie-backports main
EOF

# Refresh the list of known software
sudo apt-get update

# Okay, now we can finally install a current gphoto2
sudo apt-get install -t jessie-backports gphoto2

