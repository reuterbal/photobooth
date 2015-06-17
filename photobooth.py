#!/usr/bin/env python
# Created by br@re-web.eu, 2015

from __future__ import division

import os
from datetime import datetime
from glob import glob
from sys import exit
from time import sleep

from PIL import Image

from gui import GUI_PyGame as GuiModule

from camera import Camera_gPhoto as CameraModule
from camera import CameraException

from events import Rpi_GPIO as GPIO

#####################
### Configuration ###
#####################

# Screen size
display_size = (1024, 600)

# Maximum size of assembled image
image_size = (2352, 1568)

# Image basename
picture_basename = datetime.now().strftime("%Y-%m-%d/pic")

# GPIO channel of switch to shutdown the Pi
gpio_shutdown_channel = 24 # pin 18 in all Raspi-Versions

# GPIO channel of switch to take pictures
gpio_trigger_channel = 23 # pin 16 in all Raspi-Versions

# GPIO output channel for (blinking) lamp
gpio_lamp_channel = 4 # pin 7 in all Raspi-Versions

# Waiting time in seconds for posing
pose_time = 5

# Display time for taken pictures
display_time = 10

###############
### Classes ###
###############

class PictureList:
    """Class to manage images and count them"""
    def __init__(self, basename):
        # Set basename and suffix
        self.basename = basename
        self.suffix = ".jpg"
        self.count_width = 5
        # Ensure directory exists
        dirname = os.path.dirname(self.basename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        # Find existing files
        count_pattern = "[0-9]" * self.count_width
        pictures = glob(self.basename + count_pattern + self.suffix)
        # Get number of latest file
        if len(pictures) == 0:
            self.counter = 0
        else:
            pictures.sort()
            last_picture = pictures[-1]
            self.counter = int(last_picture[-(self.count_width+len(self.suffix)):-len(self.suffix)])
        print("Number of last existing file: " + str(self.counter) + "(" + str(len(pictures)) + ")")
        print("Saving as: " + self.basename)

    def get(self, count):
        return self.basename + str(count).zfill(self.count_width) + self.suffix

    def get_last(self):
        return self.get(self.counter)

    def get_next(self):
        self.counter += 1
        return self.get(self.counter)


class Photobooth:
    def __init__(self, picture_basename, picture_size, trigger_channel, shutdown_channel, lamp_channel):
        self.display      = GuiModule('Photobooth', display_size)
        self.pictures     = PictureList(picture_basename)
        self.camera       = CameraModule()
        self.pic_size     = picture_size

        self.trigger_channel  = trigger_channel
        self.shutdown_channel = shutdown_channel
        self.lamp_channel     = lamp_channel

        input_channels    = [ trigger_channel, shutdown_channel ]
        output_channels   = [ lamp_channel ]
        self.gpio         = GPIO(self.handle_gpio, input_channels, output_channels)

    def teardown(self):
        self.display.teardown()
        self.gpio.teardown()
        exit(0)

    def run(self):
        while True:
            try:
                # Enable lamp
                self.gpio.set_output(self.lamp_channel, 1)

                while True:
                    # Display default message
                    self.display.clear()
                    self.display.show_message("Hit the button!")
                    self.display.apply()
                    # Wait for an event and handle it
                    event = self.display.wait_for_event()
                    self.handle_event(event)

            except CameraException as e:
                self.handle_exception(e.message)

    def handle_gpio(self, channel):
        if channel in [ self.trigger_channel, self.shutdown_channel ]:
            self.display.trigger_event(channel)

    def handle_event(self, event):
        if event.type == 0:
            self.teardown()
        elif event.type == 1:
            self.handle_keypress(event.value)
        elif event.type == 2:
            self.handle_mousebutton(event.value[0], event.value[1])
        elif event.type == 3:
            self.handle_gpio_event(event.value)

    def handle_keypress(self, key):
        """Implements the actions for the different keypress events"""
        # Exit the application
        if key == ord('q'):
            self.teardown()
        # Take pictures
        elif key == ord('c'):
            self.take_picture()

    def handle_mousebutton(self, key, pos):
        """Implements the actions for the different mousebutton events"""
        # Take a picture
        if key == 1:
            self.take_picture()

    def handle_gpio_event(self, channel):
        """Implements the actions taken for a GPIO event"""
        if channel == gpio_trigger_channel:
            self.take_picture()
        elif channel == gpio_shutdown_channel:
            self.display.clear()

    def handle_exception(self, msg):
        """Displays an error message and returns"""
        self.display.clear()
        print("Error: " + msg)
        self.display.show_message("ERROR:\n\n" + msg)
        self.display.apply()
        sleep(3)


    def assemble_pictures(self, input_filenames, output_filename):
        """Assembles four pictures into a 2x2 grid"""

        # Thumbnail size of pictures
        size = (int(image_size[0]/2),int(image_size[1]/2))

        # Create output image
        output_image = Image.new('RGB', image_size)

        # Load images and resize them
        for i in range(2):
            for j in range(2):
                k = i * 2 + j
                img = Image.open(input_filenames[k])
                img.thumbnail(size)
                offset = (j * size[0], i * size[1])
                output_image.paste(img, offset)

        output_image.save(output_filename, "JPEG")

    def take_picture(self):
        """Implements the picture taking routine"""
        # Disable lamp
        self.gpio.set_output(self.lamp_channel, 0)

        # Show pose message
        self.display.clear()
        self.display.show_message("POSE!\n\nTaking four pictures...");
        self.display.apply()
        sleep(pose_time - 3)

        # Countdown
        for i in range(3):
            self.display.clear()
            self.display.show_message(str(3 - i))
            self.display.apply()
            sleep(1)

        # Show 'Cheese'
        self.display.clear()
        self.display.show_message("S M I L E !")
        self.display.apply()

        # Extract display and image sizes
        size = self.display.get_size()
        outsize = (int(size[0]/2), int(size[1]/2))

        # Take pictures
        filenames = [i for i in range(4)]
        for x in range(4):
            filenames[x] = self.camera.take_picture("/tmp/photobooth_%02d.jpg" % x)

        # Show 'Wait'
        self.display.clear()
        self.display.show_message("Please wait!\n\nProcessing...")
        self.display.apply()

        # Assemble them
        outfile = self.pictures.get_next()
        self.assemble_pictures(filenames, outfile)

        # Show pictures for 10 seconds
        self.display.clear()
        self.display.show_picture(outfile, size, (0,0))
        self.display.apply()
        sleep(display_time)

        # Reenable lamp
        self.gpio.set_output(self.lamp_channel, 1)




#################
### Functions ###
#################

def main():
    photobooth = Photobooth(picture_basename, image_size, gpio_trigger_channel, gpio_shutdown_channel, gpio_lamp_channel)
    photobooth.run()
    return photobooth.teardown()

if __name__ == "__main__":
    exit(main())