#!/usr/bin/env python
# Created by br@re-web.eu, 2015

import sys
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

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

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

# class Camera:
#     """Camera class providing functionality to take pictures"""
    # def __init__(self):



#################
### Functions ###
#################

def actions():
    display.show_picture('../../capture_preview.jpg', image_size, image_offset)

def handle_keypress(key):
    if key == ord('q'):
        display.teardown()
        sys.exit()
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

if __name__ == "__main__":
    sys.exit(main())