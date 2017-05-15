#!/usr/bin/env python
# Created by br _at_ re-web _dot_ eu, 2015-2016

import os
import pygame
from datetime import datetime
from glob import glob
from sys import exit
from time import sleep, clock

from PIL import Image

from gui import GUI_PyGame as GuiModule
from camera import CameraException, Camera_cv as CameraModule
# from camera import CameraException, Camera_gPhoto as CameraModule
from slideshow import Slideshow
from events import Rpi_GPIO as GPIO

# Printing depends on the optional python-cups module
try:
    import cups
except ImportError:
    cups=None
    print "cups module missing, so photo printing is disabled. To fix, please run:"
    print "sudo apt-get install python-cups"



#####################
### Configuration ###
#####################

# Screen size (set to 0,0 to use native resolution)
display_size = (0, 0)
#display_size = (1824, 984)

# Maximum size of assembled image
image_size = (2352, 1568)

# Size of pictures in the assembled image
thumb_size = (1176, 784)

# Image basename
picture_basename = datetime.now().strftime("%Y-%m-%d/pic")

# GPIO channel of switch to shutdown the Photobooth
gpio_shutdown_channel = 24 # pin 18 in all Raspi-Versions

# GPIO channel of switch to take pictures
gpio_trigger_channel = 23 # pin 16 in all Raspi-Versions

# GPIO output channel for (blinking) lamp
gpio_lamp_channel = 4 # pin 7 in all Raspi-Versions

# Waiting time in seconds for posing
pose_time = 3

# Display time for assembled picture
display_time = 10

# Show a slideshow of existing pictures when idle
idle_slideshow = True

# Display time of pictures in the slideshow
slideshow_display_time = 5

# Default to sending every montage to the printer?
auto_print = True

# What filename for the shutter sound when taking pictures?
# Set to None to have no sound.
shutter_sound = "shutter.wav"
#shutter_sound = None

# Temp directory for storing pictures
if os.access("/dev/shm", os.W_OK):
    tmp_dir = "/dev/shm/"       # Don't abuse Raspberry Pi SD card, if possible
else:
    tmp_dir = "/tmp/"
    

###############
### Classes ###
###############

class PictureList:
    """A simple helper class.

    It provides the filenames for the assembled pictures and keeps count
    of taken and previously existing pictures.
    """

    def __init__(self, basename):
        """Initialize filenames to the given basename and search for
        existing files. Set the counter accordingly.
        """

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

        # Print initial infos
        print("Info: Number of last existing file: " + str(self.counter))
        print("Info: Saving assembled pictures as: " + self.basename + "XXXXX.jpg")

    def get(self, count):
        return self.basename + str(count).zfill(self.count_width) + self.suffix

    def get_last(self):
        return self.get(self.counter)

    def get_next(self):
        self.counter += 1
        return self.get(self.counter)


class PictureList:
    """A simple helper class.

    It provides the filenames for the assembled pictures and keeps count
    of taken and previously existing pictures.
    """

    def __init__(self, basename):
        """Initialize filenames to the given basename and search for
        existing files. Set the counter accordingly.
        """

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

        # Print initial infos
        print("Info: Number of last existing file: " + str(self.counter))
        print("Info: Saving assembled pictures as: " + self.basename + "XXXXX.jpg")

    def get(self, count):
        return self.basename + str(count).zfill(self.count_width) + self.suffix

    def get_last(self):
        return self.get(self.counter)

    def get_next(self):
        self.counter += 1
        return self.get(self.counter)


class PrinterModule:
    """Encapsulate all the photobooth printing functionality.

    It allows the photobooth to enqueue a JPG to be printed on the
    locally connected printer.
    """

    c=None                      # This module's connection to CUPS
    printer=None                # The default printer to print to
    options = {}                # Options for printing

    def __init__(self):
        """Initialize printer defaults
        """

        # If we don't have python-cups installed, don't do anything
        if not cups:
            print ("Notice: python-cups is not installed, so printing is disabled")
            print ("To fix, run: sudo apt-get install python-cups")
            return

        # Create the connection to the default CUPS server
        try:
            self.c = cups.Connection()
        except RuntimeError as e:
            self.c = False
            print ("Error: Could not connect to CUPS server for printing: " + repr(e))
            print ("To fix, run: sudo apt-get install cups")
            return

        # Discover available printers 
        # Use default destination, if no queue is already defined
        if not self.printer:
            self.printer=self.c.getDefault()
        if not self.printer:
            # NO DEFAULT PRINTER! Let the user know how to fix it.
            if not self.c.getDests():
                print "Error: CUPS is running, but no printers are setup yet."
                print "To fix this error, first run: sudo addgroup $USER lpadmin"
                print "then, go to http://localhost:631/admin"
                return
            else:
                print "AVAILABLE PRINTERS"
                print self.c.getDests()
                print "Error: CUPS is running and at least one printer exists, but there is no server default printer."
                print "To fix this error: go to http://localhost:631/printers"
                return

        print "Printing enabled to: " + self.printer
    
        # Set default printing options
        if not self.options:
            self.options = {}
        
    def can_print(self):
        "Return True if printing is possible (CUPS running and default printer exists)"
        return self.c and self.printer

    def enqueue(self, filename):
        "Send a JPEG file to the printer using CUPS."
        if self.can_print():
            print "Now printing file " + filename + " to printer " + self.printer + ", using options " + repr(self.options)
            try: 
                self.c.printFile(self.printer, filename, filename, self.options)
            except cups.IPPError as e:
                print ("Error: Failed to print " + filename + ": " + repr(e))
                
class Photobooth:
    """The main class.

    It contains all the logic for the photobooth.
    """

    def __init__(self, display_size, picture_basename, picture_size, pose_time, display_time,
                 trigger_channel, shutdown_channel, lamp_channel, idle_slideshow, slideshow_display_time):
        self.display      = GuiModule('Photobooth', display_size)
        if (display_size == (0,0)):
            display_size = self.display.get_size()    # Get actual resolution
        self.pictures     = PictureList(picture_basename)
        self.camera       = CameraModule(picture_size)

        self.pic_size     = picture_size
        self.pose_time    = pose_time
        self.display_time = display_time

        self.trigger_channel  = trigger_channel
        self.shutdown_channel = shutdown_channel
        self.lamp_channel     = lamp_channel

        self.idle_slideshow = idle_slideshow
        if self.idle_slideshow:
            self.slideshow_display_time = slideshow_display_time
            self.slideshow = Slideshow(display_size, display_time, 
                                       os.path.dirname(os.path.realpath(picture_basename)))

        input_channels    = [ trigger_channel, shutdown_channel ]
        output_channels   = [ lamp_channel ]
        self.gpio         = GPIO(self.handle_gpio, input_channels, output_channels)

        self.printer_module  = PrinterModule()
        try:
            pygame.mixer.init()
            self.shutter = pygame.mixer.Sound(shutter_sound)
            self.shutter.play()
        except pygame.error:
            self.shutter = None
            pass
        
    def teardown(self):
        self.display.msg("Shutting down...")
        self.gpio.set_output(self.lamp_channel, 0)
        sleep(0.5)
        self.display.teardown()
        self.gpio.teardown()
        self.remove_tempfiles()
        exit(0)

    def remove_tempfiles(self):
        for filename in glob(tmp_dir + "photobooth_*.jpg"):
            try:
                os.remove(filename)
            except OSError:
                pass
            
    def _run_plain(self):
        while True:
            self.camera.set_idle()

            # Display default message
            self.display.msg("Hit the button!")

            # Wait for an event and handle it
            event = self.display.wait_for_event()
            self.handle_event(event)

    def _run_slideshow(self):
        while True:
            self.camera.set_idle()
            self.slideshow.display_next("Hit the button!")
            tic = clock()
            while clock() - tic < self.slideshow_display_time:
                self.check_and_handle_events()

    def run(self):
        while True:
            try:
                # Enable lamp
                self.gpio.set_output(self.lamp_channel, 1)

                # Select idle screen type
                if self.idle_slideshow:
                    self._run_slideshow()
                else:
                    self._run_plain()

            # Catch exceptions and display message
            except CameraException as e:
                self.handle_exception(e.message)
            # Do not catch KeyboardInterrupt and SystemExit
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as e:
                print('SERIOUS ERROR: ' + repr(e))
                self.handle_exception("SERIOUS ERROR!\n(see log file)")

    def check_and_handle_events(self):
        r, e = self.display.check_for_event()
        while r:
            self.handle_event(e)
            r, e = self.display.check_for_event()

    def clear_event_queue(self):
        r, e = self.display.check_for_event()
        while r:
            r, e = self.display.check_for_event()

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
        # Toggle autoprinting
        elif key == ord('p'):
            self.toggle_auto_print()
        elif key == ord('1'):   # Just for debugging
            self.show_preview_fps_1(5)
        elif key == ord('2'):   # Just for debugging
            self.show_preview_fps_2(5)
        elif key == ord('3'):   # Just for debugging
            self.show_preview_fps_3(5)

    def toggle_auto_print(self):
        "Toggle auto print and show an error message if printing isn't possible."
        if self.printer_module.can_print():
            global auto_print
            auto_print = not auto_print
            self.display.msg("Autoprinting %s" % ("enabled" if auto_print else "disabled"))
        else:
            self.display.msg("Printing not configured\n(see log file)")

    def handle_mousebutton(self, key, pos):
        """Implements the actions for the different mousebutton events"""
        # Take a picture
        if key == 1:
            self.take_picture()

    def handle_gpio_event(self, channel):
        """Implements the actions taken for a GPIO event"""
        if channel == self.trigger_channel:
            self.take_picture()
        elif channel == self.shutdown_channel:
            self.teardown()

    def handle_exception(self, msg):
        """Displays an error message and returns"""
        print("Error: " + msg)
        self.display.msg("ERROR:\n\n" + msg)
        sleep(3)


    def assemble_pictures(self, input_filenames):
        """Assembles four pictures into a 2x2 grid

        It assumes, all original pictures have the same aspect ratio as
        the resulting image.

        For the thumbnail sizes we have:
        h = (H - 2 * a - 2 * b) / 2
        w = (W - 2 * a - 2 * b) / 2

                                    W
               |---------------------------------------|

          ---  +---+-------------+---+-------------+---+  ---
           |   |                                       |   |  a
           |   |   +-------------+   +-------------+   |  ---
           |   |   |             |   |             |   |   |
           |   |   |      0      |   |      1      |   |   |  h
           |   |   |             |   |             |   |   |
           |   |   +-------------+   +-------------+   |  ---
         H |   |                                       |   |  2*b
           |   |   +-------------+   +-------------+   |  ---
           |   |   |             |   |             |   |   |
           |   |   |      2      |   |      3      |   |   |  h
           |   |   |             |   |             |   |   |
           |   |   +-------------+   +-------------+   |  ---
           |   |                                       |   |  a
          ---  +---+-------------+---+-------------+---+  ---

               |---|-------------|---|-------------|---|
                 a        w       2*b       w        a
        """

        # Thumbnail size of pictures
        outer_border = 50
        inner_border = 20
        thumb_box = ( int( self.pic_size[0] / 2 ) ,
                      int( self.pic_size[1] / 2 ) )
        thumb_size = ( thumb_box[0] - outer_border - inner_border ,
                       thumb_box[1] - outer_border - inner_border )

        # Create output image with white background
        output_image = Image.new('RGB', self.pic_size, (255, 255, 255))

        # Image 0
        img = Image.open(input_filenames[0])
        img.thumbnail(thumb_size)
        offset = ( thumb_box[0] - inner_border - img.size[0] ,
                   thumb_box[1] - inner_border - img.size[1] )
        output_image.paste(img, offset)

        # Image 1
        img = Image.open(input_filenames[1])
        img.thumbnail(thumb_size)
        offset = ( thumb_box[0] + inner_border,
                   thumb_box[1] - inner_border - img.size[1] )
        output_image.paste(img, offset)

        # Image 2
        img = Image.open(input_filenames[2])
        img.thumbnail(thumb_size)
        offset = ( thumb_box[0] - inner_border - img.size[0] ,
                   thumb_box[1] + inner_border )
        output_image.paste(img, offset)

        # Image 3
        img = Image.open(input_filenames[3])
        img.thumbnail(thumb_size)
        offset = ( thumb_box[0] + inner_border ,
                   thumb_box[1] + inner_border )
        output_image.paste(img, offset)

        # Save assembled image
        output_filename = self.pictures.get_next()
        output_image.save(output_filename, "JPEG")
        return output_filename

    def show_preview(self, message=""):
        """If camera allows previews, take a photo and show it so people can
        pose before the shot. For speed, previews are decimated to fit
        within the screen instead of being scaled. For even more
        speed, the previews are blitted directly to a subsurface of
        the display. (Converting to a pygame Surface would have been slow). 

        """ 
        self.display.clear()
        if self.camera.has_preview():
            f = self.camera.get_preview_array(self.display.get_size())
            self.display.blit_array(f)
        self.display.show_message(message)
        self.display.apply()

    def show_counter(self, seconds):
        """Loop over showing the preview (if possible), with a count down"""
        tic = clock()
        toc = clock() - tic
        while toc < seconds:
            self.show_preview(str(seconds - int(toc)))
            # Limit progress to 1 "second" per preview (e.g., too slow on Raspi 1)
            toc = min(toc + 1, clock() - tic)

    def show_preview_fps_1(self, seconds):
        """XXX Debugging code for benchmarking XXX

        This is the original show_countdown preview code. 

        Using camera.take_preview(), display.show_picture() is very
        slow. How slow? 5 frames per second! This is true even when
        using shared memory instead of /tmp. 

        While show_message() and clear() also drop fps significantly,
        they are not as much of a bottleneck.

        On an iMac:
        * take_preview() -5 fps
        * show_picture() -9 fps
        * show_message() -2 fps
        * clear()	 -0.5 fps

        """
        import cv2, pygame, numpy
        tic = clock()
        toc = 0
        frames=0

        while toc < seconds:
            frames=frames+1

            self.display.clear()
            if self.camera.has_preview():
                self.camera.take_preview(tmp_dir + "photobooth_preview.jpg")
                self.display.show_picture(tmp_dir + "photobooth_preview.jpg", flip=True) 
            self.display.show_message(str(seconds - int(toc)))
            self.display.apply()

            toc = clock() - tic

        self.display.msg("FPS: %d/%.2f = %.2f" % (frames, toc, float(frames)/toc))
        print("FPS: %d/%.2f = %.2f" % (frames, toc, float(frames)/toc))
        sleep(3)

    def show_preview_fps_2(self, seconds):
        """XXX Debugging code for benchmarking XXX

        This is the slower method, using make_surface
        (It's faster to use subsurfaces, see below).

        As a test, I'm trying a direct conversion from OpenCV to a
        PyGame Surface in memory and it's much faster. >20fps

        Note that the conversion (cvtColor, rot90) takes up time.
        Without the conversion, the loop is limited by the speed from
        which we can read from the camera (about 30fps).

        Blitting a static image without reading from a camera is
        giving me about 180fps on a Raspberry Pi3b.

        """
        import cv2, pygame, numpy
        tic = clock()
        toc = 0
        frames=0
        
        while toc < seconds:
            frames=frames+1

            self.display.clear()

            # Capture a preview image from the camera as a pygame surface.
            s = self.camera.get_preview_pygame_surface()
            ( w,  h) = s.get_size()
            (dw, dh) = self.display.get_size()

            # Figure out maximum proportional scaling
            size=(dw, dh)
            image_size = (w, h)
            offset=(0,0)
            image_scale = min([min(a,b)/float(b) for a,b in zip(size, image_size)])
            # New image size
            new_size = [int(a*image_scale) for a in image_size]
            # Update offset
            offset = tuple(a+int((b-c)/2) for a,b,c in zip(offset, size, new_size))
            # Apply scaling
            s = pygame.transform.scale(s, new_size).convert()

            # Display it using kludge to GUI_Pygame
            self.display.surface_list.append((s, offset))

            self.display.show_message(str(seconds - int(toc)))
            self.display.apply()

            toc = clock() - tic

        self.display.msg("FPS: %d/%.2f = %.2f" % (frames, toc, float(frames)/toc))
        print("FPS: %d/%.2f = %.2f" % (frames, toc, float(frames)/toc))
        sleep(3)

    def show_preview_fps_3(self, seconds):
        """XXX Debugging code for benchmarking XXX

        This is the fastest method, which decimates the array and
        blits it directly to a subsurface of the display.

        """
        import cv2, pygame, numpy
        tic = clock()
        toc = 0
        frames=0

        while toc < seconds:
            frames=frames+1

            self.display.clear()

            # Grab a preview, decimated to fit within the screen size
            f = self.camera.get_preview_array(self.display.get_size())

            # Blit it to the center of the screen
            self.display.blit_array(f)

            self.display.show_message(str(seconds - int(toc)))
            self.display.apply()

            toc = clock() - tic

        self.display.msg("FPS: %d/%.2f = %.2f" % (frames, toc, float(frames)/toc))
        print "FPS: %d/%.2f = %.2f" % (frames, toc, float(frames)/toc)
        sleep(3)

    def show_pose(self, seconds, message=""):
        """Loop over showing the preview (if possible), with a static message.

        Note that this is *necessary* for OpenCV webcams as V4L will ramp the
        brightness level only after a certain number of frames have been taken.
        """
        tic = clock()
        toc = clock() - tic
        while toc < seconds:
            self.show_preview(message)
            # Limit progress to 1 "second" per preview (e.g., too slow on Raspi 1)
            toc = min(toc + 1, clock() - tic)

    def take_picture(self):
        """Implements the picture taking routine"""
        # Disable lamp
        self.gpio.set_output(self.lamp_channel, 0)

        # Show pose message
        self.show_pose(2, "POSE!\n\nTaking four pictures...");

        # Extract display and image sizes
        size = self.display.get_size()
        outsize = (int(size[0]/2), int(size[1]/2))

        # Take pictures
        filenames = [i for i in range(4)]
        for x in range(4):
            # Countdown
            self.show_counter(self.pose_time)

            # Try each picture up to 3 times
            remaining_attempts = 3
            while remaining_attempts > 0:
                remaining_attempts = remaining_attempts - 1

                self.display.clear((255,230,200))
                self.display.show_message("S M I L E !!!\n\n" + str(x+1) + " of 4")
                self.display.apply()

                tic = clock()

                try:
                    filenames[x] = self.camera.take_picture(tmp_dir + "photobooth_%02d.jpg" % x)
                    remaining_attempts = 0
                    if self.shutter:
                        self.shutter.play()
                except CameraException as e:
                    # On recoverable errors: display message and retry
                    if e.recoverable:
                        if remaining_attempts > 0:
                            self.display.msg(e.message)  
                            sleep(5)
                        else:
                            raise CameraException("Giving up! Please start over!", False)
                    else:
                       raise e

                # Measure used time and sleep a second if too fast 
                toc = clock() - tic
                if toc < 1.0:
                    sleep(1.0 - toc)

        # Show 'Wait'
        self.display.msg("Please wait!\n\nProcessing...")

        # Assemble them
        outfile = self.assemble_pictures(filenames)

        if self.printer_module.can_print():
            # Show picture for 10 seconds and then send it to the printer.
            # If auto_print is True,  hitting the button cancels the print.
            # If auto_print is False, hitting the button sends the print
            tic = clock()
            t = int(self.display_time - (clock() - tic))
            old_t = self.display_time+1
            button_pressed=False

            # Clear event queue (in case they hit the button twice accidentally) 
            self.clear_event_queue()

            while t > 0:
                if t != old_t:
                    self.display.clear()
                    self.display.show_picture(outfile, size, (0,0))
                    self.display.show_message("%s%d" % ("Printing in " if auto_print else "Print photo?\n", t))
                    self.display.apply()
                    old_t=t
                
                # Watch for button, gpio, mouse press to cancel/enable printing
                r, e = self.display.check_for_event()
                if r:
                    self.display.clear()
                    self.display.show_picture(outfile, size, (0,0))
                    self.display.show_message("Printing%s" % (" cancelled" if auto_print else ""))
                    self.display.apply()
                    sleep(1)
                
                    # Discard extra events (e.g., they hit the button a bunch)
                    self.clear_event_queue() 

                    button_pressed=True
                    break

                t = int(self.display_time - (clock() - tic))

            if auto_print ^ button_pressed:
                self.printer_module.enqueue(outfile)
        else:
            # No printer available, so just show montage for 10 seconds
            self.display.clear()
            self.display.show_picture(outfile, size, (0,0))
            self.display.apply()
            sleep(self.display_time)

        # Reenable lamp
        self.gpio.set_output(self.lamp_channel, 1)




#################
### Functions ###
#################

def main():
    photobooth = Photobooth(display_size, picture_basename, image_size, pose_time, display_time, 
                            gpio_trigger_channel, gpio_shutdown_channel, gpio_lamp_channel, 
                            idle_slideshow, slideshow_display_time)
    photobooth.run()
    photobooth.teardown()
    return 0

if __name__ == "__main__":
    exit(main())
