# photobooth
A Raspberry-Pi powered photobooth using gPhoto 2.

## Description
Python application to build your own photobooth using a [Raspberry Pi](https://www.raspberrypi.org/), [gPhoto2](http://gphoto.sourceforge.net/) and [pygame](https://www.pygame.org).

The code was developed from scratch but inspired by the following tutorials/projects:
* http://www.instructables.com/id/Raspberry-Pi-photo-booth-controller/
* http://www.drumminhands.com/2014/06/15/raspberry-pi-photo-booth/
* https://www.renesasse.de/diy-die-eigene-photo-booth-box/

## Requirements

### Software stack
The following is required for running this photobooth application. I used the versions given in brackets, others might work just as well.

* [Python](https://www.python.org) (2.7.3)
* [Pygame](https://www.pygame.org) (1.9.1)
* [Pillow](http://pillow.readthedocs.org) (2.8.1)
* [gPhoto](http://gphoto.sourceforge.net/) (2.5.6)
* Optional: [RPi.GPIO](https://pypi.python.org/pypi/RPi.GPIO) (0.5.11)

RPi.GPIO is necessary to use external buttons as a trigger but it works just fine without. Triggering is then only possible using touch screen / mouse or key 'c'.

### Hardware
* [Raspberry Pi](https://www.raspberrypi.org/) (Any device able to run the software stack should work fine)
* Camera supported by gPhoto. I've used a Canon EOS 500D.
* Optional: External button that closes GPIO23 (pin 16) and GND.

## Usage
Simply download `photobooth.py` or clone the repository and run it.
It opens the GUI, prints the features of the connected camera, e.g.,
```
$ ./photobooth.py 
Abilities for camera             : Canon EOS 500D
Serial port support              : no
USB support                      : yes
Capture choices                  :
                                 : Image
                                 : Preview
Configuration support            : yes
Delete selected files on camera  : yes
Delete all files on camera       : no
File preview (thumbnail) support : yes
File upload support              : yes
```
and waits for you to hit the button to take pictures.

Available actions:

* Press `q`: Exit the application
* Press `c`: Take four pictures, arrange them in a grid and display them for some seconds.
* Hit a switch that closes GPIO23 (Pin 16) and GND: Take four pictures, arrange them in a grid and display them for some seconds.
* Click anywhere on the screen: Take four pictures, arrange them in a grid and display them for some seconds.
 
All pictures taken are stored in a subfolder of the current working directory, named `YYYY-mm-dd` after the current date. Existing files are not overwritten.

## Installation
A brief description on how to set-up a Raspberry Pi to use this photobooth software.

1. Download latest Raspbian image and set-up an SD-card. You can follow [these instruction](https://www.raspberrypi.org/documentation/installation/installing-images/README.md).

   If your display needs some additional configuration, change the file `config.txt` in the `boot`-partition to your needs. For example, I'm using a [Pollin LS-7T touchscreen](http://www.pollin.de/shop/dt/NTMwOTc4OTk-), for which I need to enter the following to avoid overscan:
   ```
   hdmi_group=2
   hdmi_mode=87
   hdmi_cvt=1024 600 60 6 0 0 0
   ```

2. Insert the SD-card into your Raspberry Pi and fire it up. Use the `rpi-config` tool that is shown automatically on the first boot to configure your system (e.g., expand partition, change hostname, password, enable SSH, configure to boot into GUI, etc.).

3. Reboot and open a terminal. Type `sudo rpi-update` to install the latest software versions. Reboot.

4. Run `sudo apt-get update` and `sudo apt-get upgrade` to upgrade all installed software.

5. Install any additionally required software:
  * Pillow: 
    ```
    sudo apt-get install python-dev python-pip libjpeg8-dev
    sudo pip install Pillow
    ```
  * gPhoto2: Unfortunately, the version in the repositories is too old to work (some USB-bugs), hence one must use [Gonzalos installer script]()
    ```
    git clone https://github.com/gonzalo/gphoto2-updater
    sudo gphoto2-updater/gphoto2-updater.sh
    ```
    To ensure the camera can be controlled properly via USB, remove some files:
    ```
    sudo rm /usr/share/dbus-1/services/org.gtk.Private.GPhoto2VolumeMonitor.service
    sudo rm /usr/share/gvfs/mounts/gphoto2.mount
    sudo rm /usr/share/gvfs/remote-volume-monitors/gphoto2.monitor
    sudo rm /usr/lib/gvfs/gvfs-gphoto2-volume-monitor
    ```
  * xinput_calibrator to calibrate touchscreens:
    ```
    wget http://adafruit-download.s3.amazonaws.com/xinput-calibrator_0.7.5-1_armhf.deb
    sudo dpkg -i -B xinput-calibrator_0.7.5-1_armhf.deb
    ```
    Calibrate by calling `xinput_calibrator` and pasting the showed snippet to a new file `/etc/X11/xorg.conf.d/99-calibration.conf` (Create the directory if necessary).

6. Reboot.

7. Clone the Photobooth repository
   ```
   git clone https://github.com/reuterbal/photobooth
   ```
   and run `photobooth.py`

## Modifications
In the beginning of `photobooth.py` a number of config options are available. Change them to your liking.

The GUI-class is separated from the entire functionality. I'm using Pygame because it's so simple to use. Feel free to replace it by your favorite library.

## License
I provide this code under AGPL v3. See [LICENSE](https://github.com/reuterbal/photobooth/blob/master/LICENSE).
