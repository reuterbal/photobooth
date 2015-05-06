#!/usr/bin/env python
# Created by br@re-web.eu, 2015

from __future__ import division

import sys
import subprocess
import time
import pygame

#####################
### Configuration ###
#####################

# Screen size
display_size = (800, 600)

# Image size for displaying
image_size = (640, 480)

# Display offset for pictures
image_offset = (80,60)

# Idle image
image_idle = "idle.jpg"

# Pose image
image_pose = "pose.png"

# Image basename
image_basename = "pic"

###############
### Classes ###
###############

class Images:
    """Class to manage images and count them"""
    def __init__(self, basename):
        self.basename = basename
        self.counter = 0
        self.suffix = ".jpg"

    def get(self, count):
        return self.basename + str(count).zfill(5) + self.suffix

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
        # Reset and initialize screen
        self.reset()

    def reset(self):
        self.screen = pygame.display.set_mode(self.size)
        self.screen.fill((255,255,255))

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
        max_size = (min(size[0],image_size[0]),min(size[1],image_size[1]))
        image_scale = min(max_size[0]/image_size[0], max_size[1]/image_size[1])
        # New image size
        size = (int(image_size[0] * image_scale), int(image_size[1] * image_scale))
        # Apply scaling and display picture
        image = pygame.transform.scale(image, size).convert()
        self.screen.blit(image, offset)

    def show_message(self, msg):
        font = pygame.font.Font(None, 36)
        text = font.render(msg, 1, (10, 10, 10))
        textpos = text.get_rect()
        textpos.centerx = self.screen.get_rect().centerx
        self.screen.blit(text, textpos)

    def mainloop(self, filename):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return
                elif event.type == pygame.KEYDOWN: handle_keypress(event.key)
            self.show_picture(filename)
            self.show_message("Hit me!")
            self.apply()

    def teardown(self):
        pygame.quit()

class CameraException(Exception):
    pass

class Camera:
    """Camera class providing functionality to take pictures"""
    def __init__(self):
        try:
            print(self.call_gphoto("-a", "/dev/null"))
        except CameraException as e:
            handle_exception(e.message)

    def call_gphoto(self, action, filename):
        try:
            output = subprocess.check_output("gphoto2 --force-overwrite --quiet " 
                                             + action + " --filename " + filename, 
                                             shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise CameraException("Can't call gphoto2!")
        # Check for non-fatal errors
        if "Canon EOS Capture failed: 2019" in output:
            raise CameraException("Cannot focus! Move a little bit and try again!")
        elif "ERROR" in output: 
            raise CameraException("Unknown error:\n" + output)
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

def handle_keypress(key):
    # Exit the application
    if key == ord('q'):
        teardown()
    # Take pictures
    elif key == ord('c'):
        # Show pose message
        display.reset()
        display.show_picture(image_pose)
        display.show_message("POSE! Taking four pictures...");
        display.apply()
        time.sleep(5)
        # Extract display and image sizes
        size = display.get_size()
        image_size = (int(size[0]/2), int(size[1]/2))
        # Take pictures
        filenames = [i for i in range(4)]
        for x in range(4):
            filenames[x] = camera.take_picture(images.get_next())
        # Show pictures for 10 seconds
        display.show_picture(filenames[0], image_size, (0,0))
        display.show_picture(filenames[1], image_size, (image_size[0],0))
        display.show_picture(filenames[2], image_size, (0,image_size[1]))
        display.show_picture(filenames[3], image_size, (image_size[0],image_size[1]))
        display.apply()
        time.sleep(10)
        display.reset()

def handle_exception(msg):
    display.reset()
    display.show_message("Error: " + msg)
    display.apply()
    time.sleep(3)
    display.reset()

def teardown(exit_code=0):
    display.teardown()
    sys.exit(exit_code)

def main():
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
camera = Camera()
images = Images("pic")

if __name__ == "__main__":
    sys.exit(main())