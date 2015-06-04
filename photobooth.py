#!/usr/bin/env python
# Created by br@re-web.eu, 2015

from __future__ import division

import os
import subprocess
from datetime import datetime
from glob import glob
from sys import exit
from time import sleep

from PIL import Image

import pygame  
try:
    import pygame.fastevent as eventmodule
except ImportError:
    import pygame.event as eventmodule

try:
    import RPi.GPIO as GPIO
    gpio_enabled = True
except ImportError:
    gpio_enabled = False

#####################
### Configuration ###
#####################

# Screen size
display_size = (1024, 600)

# Maximum size of assembled image
image_size = (2352, 1568)

# Idle image
image_idle = None

# Pose image
image_pose = None

# Image basename
image_basename = datetime.now().strftime("%Y-%m-%d/pic")

# GPIO channel of switch to shutdown the Pi
gpio_shutdown_channel = 24 # pin 18 in all Raspi-Versions

# GPIO channel of switch to take pictures
gpio_trigger_channel = 23 # pin 16 in all Raspi-Versions

# PyGame event used to detect GPIO triggers
gpio_pygame_event = pygame.USEREVENT

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

class TextRectException:
    def __init__(self, message = None):
        self.message = message
    def __str__(self):
        return self.message

def render_textrect(string, font, rect, text_color, background_color, justification=0):
    """Returns a surface containing the passed text string, reformatted
    to fit within the given rect, word-wrapping as necessary. The text
    will be anti-aliased.

    Source: http://www.pygame.org/pcr/text_rect/index.php

    Takes the following arguments:

    string - the text you wish to render. \n begins a new line.
    font - a Font object
    rect - a rectstyle giving the size of the surface requested.
    text_color - a three-byte tuple of the rgb value of the
                 text color. ex (0, 0, 0) = BLACK
    background_color - a three-byte tuple of the rgb value of the surface.
    justification - 0 (default) left-justified
                    1 horizontally centered
                    2 right-justified

    Returns the following values:

    Success - a surface object with the text rendered onto it.
    Failure - raises a TextRectException if the text won't fit onto the surface.
    """

    final_lines = []

    requested_lines = string.splitlines()

    # Create a series of lines that will fit on the provided
    # rectangle.

    for requested_line in requested_lines:
        if font.size(requested_line)[0] > rect.width:
            words = requested_line.split(' ')
            # if any of our words are too long to fit, return.
            for word in words:
                if font.size(word)[0] >= rect.width:
                    raise TextRectException, "The word " + word + " is too long to fit in the rect passed."
            # Start a new line
            accumulated_line = ""
            for word in words:
                test_line = accumulated_line + word + " "
                # Build the line while the words fit.    
                if font.size(test_line)[0] < rect.width:
                    accumulated_line = test_line 
                else: 
                    final_lines.append(accumulated_line) 
                    accumulated_line = word + " " 
            final_lines.append(accumulated_line)
        else: 
            final_lines.append(requested_line) 

    # Let's try to write the text out on the surface.

    surface = pygame.Surface(rect.size) 
    surface.fill(background_color) 

    accumulated_height = 0 
    for line in final_lines: 
        if accumulated_height + font.size(line)[1] >= rect.height:
            raise TextRectException, "Once word-wrapped, the text string was too tall to fit in the rect."
        if line != "":
            tempsurface = font.render(line, 1, text_color)
            if justification == 0:
                surface.blit(tempsurface, (0, accumulated_height))
            elif justification == 1:
                surface.blit(tempsurface, ((rect.width - tempsurface.get_width()) / 2, accumulated_height))
            elif justification == 2:
                surface.blit(tempsurface, (rect.width - tempsurface.get_width(), accumulated_height))
            else:
                raise TextRectException, "Invalid justification argument: " + str(justification)
        accumulated_height += font.size(line)[1]

    return surface

class GUI_PyGame:
    """The GUI class using PyGame"""
    def __init__(self, name, size):
        pygame.init()
        if hasattr(eventmodule, 'init'):
            eventmodule.init()
        # Window name
        pygame.display.set_caption(name)
        # Hide mouse cursor
        pygame.mouse.set_cursor(*pygame.cursors.load_xbm('transparent.xbm','transparent.msk'))
        # Store screen and size
        self.size = size
        self.screen = pygame.display.set_mode(self.size, pygame.FULLSCREEN)
        # Clear screen
        self.clear()

    def clear(self, color=(0,0,0)):
        self.screen.fill(color)

    def apply(self):
        pygame.display.update()

    def get_size(self):
        return self.size

    def trigger_event(self, event_id, event_channel):
        eventmodule.post(eventmodule.Event(event_id, channel=event_channel))

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

    def show_message(self, msg, color=(245,245,245), bg=(0,0,0)):
        # Choose font
        font = pygame.font.Font(None, 144)
        # Create rectangle for text
        rect = pygame.Rect((40, 40, self.size[0] - 40, self.size[1] - 40))
        # Render text
        text = render_textrect(msg, font, rect, color, bg, 1)
        self.screen.blit(text, rect.topleft)

    def mainloop(self, filename):
        while True:
            # Ignore all input that happened before entering the loop
            eventmodule.get()
            # Clear display
            self.clear()
            # Show idle-picture and message
            if filename != None:
                self.show_picture(filename)
            self.show_message("\n\nHit the button!")
            # Render everything
            self.apply()
            # Wait for event
            event = eventmodule.wait()
            # Handle the event
            if event.type == pygame.QUIT: return
            elif event.type == pygame.KEYDOWN: handle_keypress(event.key)
            elif event.type == pygame.MOUSEBUTTONUP: handle_mousebutton(event.button, event.pos)
            elif event.type == gpio_pygame_event: handle_gpio_event(event.channel)

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
            cmd = "gphoto2 --force-overwrite --quiet " + action + " --filename " + filename
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            if "ERROR" in output:
                raise subprocess.CalledProcessError(returncode=0, cmd=cmd, output=output)
        except subprocess.CalledProcessError as e:
            if "Canon EOS Capture failed: 2019" in e.output:
                raise CameraException("Can't focus! Move and try again!")
            elif "No camera found" in e.output:
                raise CameraException("No (supported) camera detected!")
            else:
                raise CameraException("Unknown error!\n" + '\n'.join(e.output.split('\n')[1:3]))
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

def assemble_pictures(input_filenames, output_filename):
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

def take_picture():
    """Implements the picture taking routine"""
    # Show pose message
    display.clear()
    if image_pose != None:
        display.show_picture(image_pose)
    display.show_message("POSE!\n\nTaking four pictures...");
    display.apply()
    sleep(pose_time - 3)

    # Countdown
    for i in range(3):
        display.clear()
        display.show_message("\n\n" + str(3 - i))
        display.apply()
        sleep(1)

    # Show 'Cheese'
    display.clear()
    display.show_message("\n\nS M I L E !")
    display.apply()

    # Extract display and image sizes
    size = display.get_size()
    outsize = (int(size[0]/2), int(size[1]/2))

    # Take pictures
    filenames = [i for i in range(4)]
    for x in range(4):
        filenames[x] = camera.take_picture("/tmp/photobooth_%02d.jpg" % x)

    # Show 'Wait'
    display.clear()
    display.show_message("Please wait!\n\nProcessing...")
    display.apply()

    # Assemble them
    outfile = images.get_next()
    assemble_pictures(filenames, outfile)

    # Show pictures for 10 seconds
    display.clear()
    display.show_picture(outfile, size, (0,0))
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

def handle_mousebutton(key, pos):
    """Implements the actions for the different mousebutton events"""
    # Take a picture
    if key == 1:
        take_picture()

def handle_gpio_event(channel):
    """Implements the actions taken for a GPIO event"""
    if channel == gpio_trigger_channel:
        take_picture()
    elif channel == gpio_shutdown_channel:
        display.clear()
        print("Shutting down!")
        display.show_message("Shutting down!")
        display.apply()
        sleep(1)
        os.system("shutdown -h now")

def handle_exception(msg):
    """Displays an error message and returns"""
    display.clear()
    print("Error: " + msg)
    display.show_message("ERROR:\n\n" + msg)
    display.apply()
    sleep(3)

def setup_gpio():
    """Enables GPIO in- and output and registers event handles"""
    if gpio_enabled:
        # Display initial information
        print("Your Raspberry Pi is board revision " + str(GPIO.RPI_INFO['P1_REVISION']))
        print("RPi.GPIO version is " + str(GPIO.VERSION))
        # Choose BCM numbering system
        GPIO.setmode(GPIO.BCM)
        # Setup the trigger channel as input and listen for events
        GPIO.setup(gpio_trigger_channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(gpio_trigger_channel, GPIO.RISING, callback=handle_gpio, bouncetime=200)
    else:
        print("Warning: RPi.GPIO could not be loaded. GPIO disabled.")

def handle_gpio(channel):
    """Interrupt handler for GPIO events"""
    display.trigger_event(gpio_pygame_event, channel)

def teardown(exit_code=0):
    display.teardown()
    if gpio_enabled:
        GPIO.cleanup()
    exit(exit_code)

def main():
    setup_gpio()
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