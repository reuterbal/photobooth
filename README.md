# photobooth
A Raspberry-Pi powered photobooth using gPhoto 2.

## Spork notice
This is intended to be a temporary fork from br's original photobooth.
Hopefully, he/she will fold my additions back into the original
project. You'll find br's original README appended below. --b9

### Major differences
* Allow portrait photos (just like a real photobooth!) by putting
camera and monitor on their side. You can either edit the
photobooth.py file and change display_rotate and camera_rotate, or
just hit the 'r' key at run time toggle rotation.
* Automatically prints to default printer if python-cups is installed.
  * The idea is that you'll set up the default queue to be a photo printer set to 4x6 (or whatever paper size you use).
  * Automatic printing can be disabled by default in the program by setting auto_print=False at the top of photobooth.py.
  * Automatic printing can be toggled at run time by hitting the 'p' key.
  * An individual print can be cancelled during a 10 second countdown. If the button is pressed (or actually any event happens) during that time, printing will be cancelled.
* Much improved display handling. Now defaults to native resolution instead
of being hardcoded to 1824x984. (You can still force a resolution by
setting display_size in photobooth.py).
* Uses /dev/shm (if available) to store preview files instead of
writing to /tmp. SD Cards, like on the Raspberry Pi, have a limited
number of writes and so it doesn't make sense to be writing 30 JPEGs
per second while people are posing.
* Helper script (jbp.sh) for Raspian (or Debian Jessie) to install a working
version of gphoto2. The photobooth program requires gphoto2 >= 2.5.6,
but it's not in the standard repositories. The original author
suggested downloading and compiling it from source, which works but
takes a very long time on a Pi. Much simpler and faster is to add the "backports"
repository and install a newer gphoto from there.
* Framerate greatly improved during preview. The original code was so
slow (at least with the webcams I was using) that posing for pictures
was difficult. (Biggest improvements from blitting an array instead of
a Pygame Surface, blitting to a subsurface of the display, and from
caching the countdown rendered text.)
* If you're curious about your frame rate, you can press '1' to test
the original blitting (but with the improved text cache), or '2' which
adds the improved array blitting, or '3' which adds subsurface
blitting. After 5 seconds, the screen will show your FPS.


### Implementation notes

In theory, reality and theory are the same. In reality, they are not.
Here are some notes on things I did to make this photobooth work
nicely on the particular hardware I have. (Raspberry Pi 3B, HP w2207h
rotatable HDMI monitor with builtin speakers, Logitech QuickCam)

* First problem: Setting up the photo printer required an ugly kludge.
  The first printer I tested (Canon Pixma MP) actually worked great
  once I set a few default options to the [CUPS
  queue](http://localhost:631/):

  * Media size: 4x6
  * Color Precision: Best
  * Media Type: Glossy Photo Paper
  * Shrink page if necessary: Shrink (print the whole page)
  * Borderless: Yes
  * Error Policy: abort-job
  
  I could just send any JPEG over and the Gutenprint driver would
  automatically rotate, scale, and center it for me. Nice!

  However, the next printer I tried, an HP Officejet 7300, did not
  have a nice Gutenprint driver. Instead, I had to use hpcups
  (`apt-get install printer-driver-hpcups)`, which apparently does not
  rotate, shrink, or center images.

* Printing solution: I made a hack that simply calls ImageMagick's
  `convert` before printing to rotate and force the media size to be
  4x6:
  
  ```
  convert filename.jpg -rotate -90 -page 4x6 filename.pdf
  ```

  This works because the print driver apparently obeys the page size
  specified in PNG and PDF files and scales appropriately.
  
  * DIGRESSION: the proper solution would perhaps have been to change
  the photobooth.py software to handle all rotate, scale, and
  centering on its own. However, that would require photobooth.py
  knowing the media size, which turns out to be rather ugly. It is
  possible to query CUPS for the current media size, but it returns
  strings which are driver dependent. For example, for Gutenprint I
  would specify "4x6", but for hpcups, I need to specify "Photo4x6.FB"
  (I believe "FB" stands for "full bleed" which means "don't add
  borders").

* Second problem: no camera. I had intended to use my nifty Canon
  PowerShot for capturing the photos. I had not known that Canon
  stopped allowing any API remote control of the PowerShot line and so
  it would not work. (Shoulda kept my old PowerShot!)

* [Here](http://gphoto.org/doc/remote) is a (partial) list of gphoto2
  compatible cameras which *can* do "remote capture" (snap a photo
  under computer control). 

* Solution: I ransacked my junk draw and came up with an old USB
  webcam (Logitech QuickCam, VGA). It worked once I switched
  photobooth.py to use OpenCV instead of Gphoto. (Thank you original
  author, BR, who thoughtfully added in that option!) However, it was
  limited to VGA resolution (640x480) and the kernel driver (gspca)
  seems a bit glitchy. (Occasional graphical artifacts, sometimes
  camera needs to be unplugged and replugged in. It may not be a
  driver problem: perhaps my power supply can't supply enough
  current?)

* Next problem: postage stamp sized previews during the "POSE" time.
  As noted above, for speed I had changed the photobooth to blit a raw
  array (not a Surface) to the pygame display. One cannot easily scale
  up raw arrays (Pygame transformations only work on Surfaces), so my
  code works great if the camera is a higher resolution than the
  display (which is what you'd normally expect). However, my lousy
  resolution QuickCam gave me a tiny island of a preview, adrift in a
  sea of black, wasted pixels.

  On a normal computer, it is possible to force the screen resolution
  to be lower by setting `display_size = (640, 480)` in photobooth.py.
  However, that does not work for my situation as the Raspberry Pi 3B
  is not able to dynamically switch the HDMI resolution.

* Solution: edit /boot/config.txt and force the HDMI mode to a lower
  resolution. I set mine to 640x480 like so:
    ```
    hdmi_group=2
    hdmi_mode=4
    ```
  I found which mode number was 640x480 by typing `tvservice -m DMT` .

* To play a nice shutter sound when taking pictures, I enabled HDMI
    audio by editing /boot/config.txt and uncommenting `hdmi_drive=2`.

* DIGRESSION: the Raspberry Pi can configure an HDMI monitor in one of
  two ways:

   * Group 1: CEA (Consumer Electronics Association), which is
     intended for televisions. CEA has the benefit of automatically
     using speakers builtin to the display. It has the downside of
     using "overscan" (a black border around the image) by default and
     not being able to show a "true" black. (Darkest color is 16, not 0).

   * Group 2: DMT (Display Monitor Timing), which is intended for
     computer monitors. CEA modes are always progressive, never
     interlaced. DMT doesn't have CEA's overscan annoyances and will
     actually use the darkest black available on your monitor. The
     downside is that DMT modes default to using the DVI "drive" which
     cannot send audio to speakers over HDMI.

     You can force a Raspberry Pi to find your monitor's speakers
     either permanently or temporarily:

     *** Permanently: uncomment or add `hdmi_drive=2` in
         /boot/config.txt and reboot.

     *** Temporarily: Use the `tvservice -e ... HDMI` command and then
         switch virtual terminals to refresh the screen.
         Unfortunately, tvservice doesn't let you change just the
         DRIVE, you have to change the GROUP and MODE simultaneously,
         so you'll need to run `tvservice -s` first to find out what
         GROUP and MODE you are using. (Note that `tvservice -s` shows
         the DRIVE at the beginning, but `tvservice -e` requires the
         DRIVE to be specified at the end.)

	 ```
	 $ tvservice -s
	 state 0x12000a [DVI DMT (58) RGB full 16:10], 1680x1050 @ 60.00Hz, progressive

	 $ tvservice -e "DMT 58 HDMI"
	 $ # Now press Ctrl-Alt-F1 then Ctrl-Alt-F7
	 ```
     

## I've appended below, nearly unchanged, br's original README file.


## Description
Python application to build your own photobooth using a [Raspberry Pi](https://www.raspberrypi.org/), [gPhoto2](http://gphoto.sourceforge.net/) and [pygame](https://www.pygame.org).

The code was developed from scratch but inspired by the following tutorials/projects:
* http://www.instructables.com/id/Raspberry-Pi-photo-booth-controller/
* http://www.drumminhands.com/2014/06/15/raspberry-pi-photo-booth/
* https://www.renesasse.de/diy-die-eigene-photo-booth-box/

## Requirements

### Software stack

    TLDR: sudo apt-get install python-pygame gphoto2 python-opencv python-cups

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
