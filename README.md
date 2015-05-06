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

### Hardware
* [Raspberry Pi](https://www.raspberrypi.org/) (Any device able to run the software stack should work fine)
* Camera supported by gPhoto. I've used a Canon EOS 500D.

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

Eventually I want to use the GPIO-pins to support external buttons, for now only two commands are supported:

* `q`: Exit the application
* `c`: Take four pictures and show them in a grid
 
All pictures taken are stored in the current working directory.

## Modifications
In the beginning of the file a number of config options are available. Change them to your liking.

The GUI-class is separated from the entire functionality. I'm using Pygame because it's so simple to use. Feel free to replace it by your favorite library.

## License
I provide this code under AGPL v3. See [LICENSE](https://github.com/reuterbal/photobooth/blob/master/LICENSE).
