#!/usr/bin/env python
# Created by br@re-web.eu, 2015

from __future__ import division

import subprocess
from datetime import datetime
from glob import glob
from sys import exit
from time import sleep

import pygame
import RPi.GPIO as GPIO

#####################
### Configuration ###
#####################

# Screen size
display_size = (1024, 600)

# Idle image
image_idle = "idle.jpg"

# Pose image
image_pose = "pose.png"

# Image basename
image_basename = datetime.now().strftime("%Y-%m-%d/pic")

# GPIO channel of switch to take pictures
gpio_trigger_channel = 7 # pin 26 in all Raspi-Versions

# Waiting time in seconds for posing
pose_time = 5

# Display time for taken pictures
display_time = 10

###############
### Classes ###
###############

class Images:
    """Class to manage images and count them"""
    def __init__(self, basename):
        # Set basename and suffix
        self.basename = basename
        self.suffix = ".jpg"
        self.count_width = 5
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

class GUI_PyGame:
    """The GUI class using PyGame"""
    def __init__(self, name, size):
        pygame.init()
        # Window name
        pygame.display.set_caption(name)
        # Hide mouse cursor
        pygame.mouse.set_visible(False)
        # Store screen and size
        self.size = size
        self.screen = pygame.display.set_mode(self.size, pygame.FULLSCREEN)
        # Clear screen
        self.clear()

    def clear(self, color=(255,255,255)):
        self.screen.fill(color)

    def apply(self):
        pygame.display.update()

    def get_size(self):
        return self.size

    def show_picture(self, filename, size=(0,0), offset=(0,0)):
        # Use window size if none given
        if size == (0,0):
            size = self.size
        # Load image from file
        image = pygame.image.load(filename)
        # Extract image size and determine scaling
        image_size = image.get_rect().size
        image_scale = min([min(a,b)/b for a,b in zip(size, image_size)])
        # New image size
        new_size = [int(a*image_scale) for a in image_size]
        # Update offset
        offset = tuple(a+int((b-c)/2) for a,b,c in zip(offset, size, new_size))
        # Apply scaling and display picture
        image = pygame.transform.scale(image, new_size).convert()
        self.screen.blit(image, offset)

    def show_message(self, msg):
        # Choose font
        font = pygame.font.Font(None, 36)
        # Render text
        text = font.render(msg, 1, (10, 10, 10))
        # Position and display text
        textpos = text.get_rect()
        textpos.centerx = self.screen.get_rect().centerx
        self.screen.blit(text, textpos)

    def mainloop(self, filename):
        while True:
            # Clear display
            self.clear()
            # Show idle-picture and message
            self.show_picture(filename)
            self.show_message("Hit me!")
            # Render everything
            self.apply()
            # Wait for event
            event = pygame.event.wait()
            # Handle the event
            if event.type == pygame.QUIT: return
            elif event.type == pygame.KEYDOWN: handle_keypress(event.key)
            # Ignore all input that happened inbetween
            pygame.event.clear()

    def teardown(self):
        pygame.quit()

class CameraException(Exception):
    """Custom exception class to handle gPhoto errors"""
    pass

class Camera:
    """Camera class providing functionality to take pictures"""
    def __init__(self):
        # Print the abilities of the connected camera
        try:
            print(self.call_gphoto("-a", "/dev/null"))
        except CameraException as e:
            handle_exception(e.message)

    def call_gphoto(self, action, filename):
        # Try to run the command
        try:
            output = subprocess.check_output("gphoto2 --force-overwrite --quiet " 
                                             + action + " --filename " + filename, 
                                             shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise CameraException("Can't call gphoto2!")
        # Handle non-fatal errors
        if "Canon EOS Capture failed: 2019" in output:
            raise CameraException("Cannot focus! Move a little bit and try again!")
        elif "ERROR" in output: 
            raise CameraException("Unknown error:\n" + output)
        # Return the command line output
        return output

    def preview(self, filename="/tmp/preview.jpg"):
	while not self.call_gphoto("--capture-preview", filename):
	    continue
        return filename

    def take_picture(self, filename="/tmp/picture.jpg"):
        self.call_gphoto("--capture-image-and-download", filename)
        return filename


#################
### Functions ###
#################

def take_picture():
    display.clear()
    # Show pose message
    display.show_picture(image_pose)
    display.show_message("POSE! Taking four pictures...");
    display.apply()
    sleep(pose_time)
    # Extract display and image sizes
    size = display.get_size()
    image_size = (int(size[0]/2), int(size[1]/2))
    # Take pictures
    filenames = [i for i in range(4)]
    for x in range(4):
        filenames[x] = camera.take_picture(images.get_next())
    # Show pictures for 10 seconds
    display.clear()
    display.show_picture(filenames[0], image_size, (0,0))
    display.show_picture(filenames[1], image_size, (image_size[0],0))
    display.show_picture(filenames[2], image_size, (0,image_size[1]))
    display.show_picture(filenames[3], image_size, (image_size[0],image_size[1]))
    display.apply()
    sleep(display_time)

def handle_keypress(key):
    """Implements the actions for the different keypress events"""
    # Exit the application
    if key == ord('q'):
        teardown()
    # Take pictures
    elif key == ord('c'):
        take_picture()

def handle_gpio_event(channel):
    """Implements the actions taken for a GPIO event"""
    if channel == gpio_trigger_channel:
        GPIO.remove_event_detect(gpio_trigger_channel)
        take_picture()
        GPIO.add_event_detect(gpio_trigger_channel, GPIO.RISING, 
                              callback=handle_gpio_event, bouncetime=200)
        
def handle_exception(msg):
    """Displays an error message and returns"""
    display.clear()
    msg = "Error: " + msg
    print(msg)
    display.show_message(msg)
    display.apply()
    sleep(3)

def setup_gpio():
    # Display initial information
    print "Your Raspberry Pi is board revision " + str(GPIO.RPI_INFO['P1_REVISION'])
    print "RPi.GPIO version is " + str(GPIO.VERSION)
    # Choose BCM numbering system
    GPIO.setmode(GPIO.BCM)
    # Setup the trigger channel as input and listen for events
    GPIO.setup(gpio_trigger_channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(gpio_trigger_channel, GPIO.RISING, 
                          callback=handle_gpio_event, bouncetime=200)

def teardown(exit_code=0):
    display.teardown()
    #GPIO.cleanup()
    exit(exit_code)

def main():
    #setup_gpio()
    while True:
        try:
            display.mainloop(image_idle)
        except CameraException as e:
            handle_exception(e.message)
    display.teardown()
    return 0

########################
### Global variables ###
########################

display = GUI_PyGame('Photobooth', display_size)
images = Images(image_basename)
camera = Camera()

if __name__ == "__main__":
    exit(main())