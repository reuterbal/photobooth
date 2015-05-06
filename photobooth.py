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
        if size == (0,0):
            size = self.size
        image = pygame.image.load(filename)
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

# def error(msg, exit_code=1):
#     print "ERROR: " + msg
#     teardown(exit_code)

def handle_keypress(key):
    if key == ord('q'):
        teardown()
    elif key == ord('c'):
        print "Taking 4 pictures"
        size = display.get_size()
        image_size = (int(size[0]/2), int(size[1]/2))
        filenames = []
        for x in range(4):
            filenames[x] = camera.take_picture(images.get_next())
        display.show_picture(filenames[0], image_size, (0,0))
        display.show_picture(filenames[1], image_size, (image_size[0],0))
        display.show_picture(filenames[2], image_size, (0,image_size[1]))
        display.show_picture(filenames[3], image_size, (image_size[0],image_size[1]))
        display.apply()
        timer.sleep(5)

def handle_exception(msg):
    display.reset()
    display.show_message("Error: " + msg)
    display.apply()
    time.sleep(3)

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