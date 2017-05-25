#!/bin/bash

cd $(dirname $0)        # Directory of this script

if [[ $1 == "set-time" ]]; then
  sudo python set-time.py
fi

if v4l2-ctl --silent 2>/dev/null; then
    # If camera uses JPEG compression, improve the quality
    v4l2-ctl -c compression_quality=100 2>/dev/null
fi


# Do some error checking to make sure gphoto will work.
# First: are they even using gphoto (not opencv)?
gphototest=$(gphoto2 --auto-detect | tail -n+3)
if [ "$gphototest" ]  >/dev/null; then
    # Yup, there's a gphoto camera available. Is it unusable?
    if ! gphoto2 --reset >/dev/null; then
        # Oh noes! Camera not usable. Somebody else has the USB bus!
        # Check if gvfs is turned on, as that can cause gphoto problems.
        autogvfs=$(gsettings get org.gnome.desktop.media-handling automount 2>/dev/null)
        if [ "$autogvfs" = "true" ]; then
            tput bel
            cat <<EOF >&2
WARNING! GNOME's desktop media-handling had been set to automatically
mount any cameras connected using GVFS. Since GVFS blocks the
photobooth access to most cameras, we are permanently disabling it.

If you decide you want to reenable automounting, you can run:

    gsettings set org.gnome.desktop.media-handling automount true

EOF
            gsettings set org.gnome.desktop.media-handling automount false
            killall gvfsd-gphoto2 gvfs-gphoto2-volume-monitor 2>/dev/null
            if ! gphoto2 --reset; then
                echo "UH OH! We still weren't able to access the camera."
                echo "Maybe try unplugging it and replugging it in?"
                echo
                echo "WARNING: Camera is inaccesible. Photobooth will likely fail."
                echo
            fi
            tput bel
            sleep 5
        fi
    else
        # Camera not accessible, but Gnome automount is NOT enabled.
        # Try killing the usual suspects anyhow and see if it works.
        killall gvfsd-gphoto2 gvfs-gphoto2-volume-monitor 2>/dev/null
        if ! gphoto2 --reset; then
            # Killing the gvfs gphoto processes didn't help.
            echo "WARNING: Camera is inaccesible. Photobooth will likely fail."
            echo

            # If they have lsof installed, use that to figure out what
            # process has the device open.
            if type lsof >/dev/null 2>&1; then
                echo "Here are the processes which have the camera locked:"
                echo "----------------------------------------"
                usbid=${gphototest#*usb:} # e.g., "001,017"
                lsof /dev/bus/usb/${usbid%,*}/${usbid#*,}
                echo "----------------------------------------"
                echo "If the photobooth doesn't work. Try killing those processes."
            else

                echo "UH OH! Looks like some other process is using the camera."
                echo "If you want me to tell you which one, please install 'lsof' using:"
                echo "sudo apt-get install lsof"
            fi
        fi
    fi
fi


# This may need 'sudo' to access camera devices, but probably doesn't.
# [Note that the Gphoto2 FAQ explicitly says to NEVER run gphoto2 as
# root, which is essentially what you'd be doing by using sudo here.]
python photobooth.py >>photobooth.log 2>>photobooth.err
