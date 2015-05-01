#!/usr/bin/env python
# Created by br@re-web.eu, 2015

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
        # Save objects
        self.size = size
        self.screen = pygame.display.set_mode(size)
        #self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)

    def get_size(self):
        return self.size

    def show_picture(self, filename, size=(0,0), offset=(0,0)):
        if size == (0,0):
            size = self.get_size()
        image = pygame.image.load(filename)
        image = pygame.transform.scale(image, size)
        self.screen.blit(image, offset)
        pygame.display.flip()

    def mainloop(self, filename):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return
                elif event.type == pygame.KEYDOWN: handle_keypress(event.key)
            self.show_picture(filename)

    def teardown(self):
        pygame.quit()

class Camera:
    """Camera class providing functionality to take pictures"""
    #def __init__(self):
    def call_gphoto(self, action, filename):
        try:
            output = subprocess.check_output("gphoto2 --force-overwrite --quiet " 
                                             + action + " --filename " + filename, 
                                             shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            error("Error during preview when calling '" + e.cmd + "'!\nOutput: "
                  + e.output, e.returncode)
        if "ERROR" in output: error("Error during preview!\n" + output)

    def preview(self, filename="/tmp/preview.jpg"):
        self.call_gphoto("--capture-preview", filename)
        return filename

    def take_picture(self, filename="/tmp/picture.jpg"):
        self.call_gphoto("--capture-image-and-download", filename)
        return filename


#################
### Functions ###
#################

def error(msg, exit_code=1):
    print "ERROR: " + msg
    teardown(exit_code)

def teardown(exit_code=0):
    display.teardown()
    sys.exit(exit_code)

def handle_keypress(key):
    if key == ord('q'):
        teardown()
    elif key == ord('c'):
        print "Taking 3 pictures"
        for x in xrange(3):
            filename = camera.take_picture(images.get_next())
            display.show_picture(filename)
            time.sleep(2)

def main(): 
    display.mainloop(image_idle)
    display.teardown()
    return 0

########################
### Global variables ###
########################

display = GUI_PyGame('Photobooth', display_size)
camera = Camera()
images = Images(image_basename)

if __name__ == "__main__":
    sys.exit(main())