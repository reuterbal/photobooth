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
The following is required for running this photobooth application. I used only versions available in the package repositories of Raspbian (tested version numbers are given in brackets), others might work just as well.

* [Python](https://www.python.org) (2.7.3)
* [Pygame](https://www.pygame.org) (1.9.1)
* [gPhoto](http://gphoto.sourceforge.net/) (2.5.6)
* [Pillow](https://pypi.python.org/pypi/Pillow) (2.8.1)
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

## Modifications
In the beginning of the file a number of config options are available. Change them to your liking.

The GUI-class is separated from the entire functionality. I'm using Pygame because it's so simple to use. Feel free to replace it by your favorite library.

## License
I provide this code under AGPL v3. See [LICENSE](https://github.com/reuterbal/photobooth/blob/master/LICENSE).
