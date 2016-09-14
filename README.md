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
* [gPhoto](http://gphoto.sourceforge.net/) (2.5.6 or later) or [OpenCV](http://opencv.org)
* Optional: [RPi.GPIO](https://pypi.python.org/pypi/RPi.GPIO) (0.5.11)
* Optional: [gphoto2-cffi](https://github.com/jbaiter/gphoto2-cffi) or [Piggyphoto](https://github.com/alexdu/piggyphoto)

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

2. Insert the SD-card into your Raspberry Pi and fire it up. Use the `raspi-config` tool that is shown automatically on the first boot to configure your system (e.g., expand partition, change hostname, password, enable SSH, configure to boot into GUI, etc.).

3. Reboot and open a terminal. Type `sudo rpi-update` to install the latest software versions. Reboot.

4. Run `sudo apt-get update` and `sudo apt-get upgrade` to upgrade all installed software.

5. Install any additionally required software:
  * Pillow: 

    ```
    sudo apt-get install python-dev python-pip libjpeg8-dev
    sudo pip install Pillow
    ```

  * gPhoto2: Unfortunately, the version in the repositories is too old to work (some USB-bugs), hence one must use [Gonzalos installer script](https://github.com/gonzalo/gphoto2-updater)

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

  * [xinput_calibrator](https://www.freedesktop.org/wiki/Software/xinput_calibrator/) to calibrate touchscreens:

    ```
    wget http://adafruit-download.s3.amazonaws.com/xinput-calibrator_0.7.5-1_armhf.deb
    sudo dpkg -i -B xinput-calibrator_0.7.5-1_armhf.deb
    ```

    Calibrate by calling `xinput_calibrator` and pasting the shown snippet to a new file `/etc/X11/xorg.conf.d/99-calibration.conf` (Create the directory if necessary).

6. Reboot.

7. Clone the Photobooth repository
   ```
   git clone https://github.com/reuterbal/photobooth
   ```
   and run `photobooth.py`

8. Optional but highly recommended, as it improves performance significantly: install some Python bindings for gPhoto2. For that, either [Piggyphoto](https://github.com/alexdu/piggyphoto) or [gphoto2-cffi](https://github.com/jbaiter/gphoto2-cffi) can be used. At the moment, Piggyphoto doesn't allow to disable the sensor while idle, so gphoto2-cffi is preferred.

   8.1 Installing gphoto2-cffi:
   Install [cffi](https://bitbucket.org/cffi/cffi)
   ```
   sudo apt-get install libffi6 libffi-dev python-cffi
   ```
   Download and install gphoto2-cffi for gPhoto2
   ```
   git clone https://github.com/jbaiter/gphoto2-cffi.git
   cd gphoto2-cffi
   python setup.py build
   sudo python setup.py install
   ```

   8.2 Install Piggyphoto:
   Download [Piggyphoto](https://github.com/alexdu/piggyphoto) and put the folder `piggyphoto` into the Photobooth-directory.

9. Optionally make the software run automatically on startup. To do that, you must simply add a corresponding line in the autostart file of LXDE, which can be found at `~/.config/lxsession/LXDE-pi/autostart`. Assuming you cloned the Photobooth repository into `/home/pi/photobooth`, add the following line into the autostart-file:
   ```
   lxterminal -e "/home/pi/photobooth/photobooth.sh set-time"
   ```
   For this to work you must install `gnome-control-center` by running `sudo apt-get install gnome-control-center` (Unfortunately, this brings along a lot of dependencies - however, I haven't found any lightweight alternative that would allow to simply set date and time using the touch screen).

10. Alternatively, you can also add a Desktop shortcut. Create a file `/home/pi/Desktop/Photobooth.desktop` and enter the following:
   ```
   [Desktop Entry]
   Encoding=UTF-8
   Type=Application
   Name=Photobooth
   Exec=lxterminal -e /home/pi/photobooth/photobooth.sh set-time
   ```

## Modifications
In the beginning of `photobooth.py` a number of config options are available. Change them to your liking.

The GUI-class is separated from the entire functionality. I'm using Pygame because it's so simple to use. Feel free to replace it by your favorite library.

Instead of gPhoto2 you can also use OpenCV to capture pictures. This is the preferred way if you want to use a webcam and is particularly useful for debugging on a different machine. For that you must install OpenCV and its Python bindings (run `sudo apt-get install python-opencv`) and then change the `CameraModule`: edit `photobooth.py` and replace `Camera_gphoto as CameraModule` by `Camera_cv as CameraModule`.

## License
I provide this code under AGPL v3. See [LICENSE](https://github.com/reuterbal/photobooth/blob/master/LICENSE).
