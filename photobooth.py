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

###############
### Classes ###
###############

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

    def mainloop(self, actions):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return
                elif event.type == pygame.KEYDOWN: handle_keypress(event.key)
            actions()

    def teardown(self):
        pygame.quit()

class Camera:
    """Camera class providing functionality to take pictures"""
    #def __init__(self):
    def preview(self, filename="/tmp/preview.jpg"):
        ret = subprocess.call("gphoto2 --force-overwrite --capture-preview --quiet --filename " + filename)
        if ret != 0: error("Error during preview!", ret)
        return filename


#################
### Functions ###
#################

def actions():
    display.show_picture(camera.preview(), image_size, image_offset)
    time.sleep(0.5)

def error(msg, exit_code=1):
    print "ERROR:" + msg
    teardown(exit_code)

def teardown(exit_code=0):
    display.teardown()
    sys.exit(exit_code)

def handle_keypress(key):
    if key == ord('q'):
        teardown()
    elif key == ord('c'):
        print "Taking picture"

def main(): 
    display.mainloop(actions)
    display.teardown()
    return 0

########################
### Global variables ###
########################

display = GUI_PyGame('Photobooth', display_size)
camera = Camera()

if __name__ == "__main__":
    sys.exit(main())