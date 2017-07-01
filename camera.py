#!/usr/bin/env python
# Created by br@re-web.eu, 2015

# TODO: This really ought to be a single class with subclasses for
# each backend (opencv, gphoto-cffi, piggyphoto, gphoto cmdline).

import os
import subprocess
import pygame
import numpy
from PIL import Image

# Temp directory for storing pictures
if os.access("/dev/shm", os.W_OK):
    tmp_dir = "/dev/shm/"       # Don't abuse Raspberry Pi SD card, if possible
else:
    tmp_dir = "/tmp/"


cv_enabled = False
gphoto2cffi_enabled = False
piggyphoto_enabled = False

try:
    import cv2 as cv
    cv_enabled = True
    print('OpenCV available')
except ImportError:
    pass

try:
    import gphoto2cffi as gp
    gpExcept = gp.errors.GPhoto2Error
    gphoto2cffi_enabled = True
    print('Gphoto2cffi available')
except ImportError:
    pass

if not gphoto2cffi_enabled:
    try:
        import piggyphoto as gp
        gpExcept = gp.libgphoto2error
        piggyphoto_enabled = True
        print('Piggyphoto available')
    except ImportError:
        pass

class CameraException(Exception):
    """Custom exception class to handle camera class errors"""
    def __init__(self, message, recoverable=False):
        self.message = message
        self.recoverable = recoverable


class Camera_cv:
    def __init__(self, resolution=(10000,10000), camera_rotate=False):
        if resolution[0]>0 and resolution[1]>0:
            self.resolution = resolution   # Requested camera resolution
        else:
            self.resolution = (10000,10000) # Just use highest resolution possible
        self.rotate = camera_rotate        # Is camera on its side?  

        global cv_enabled
        if cv_enabled:
            self.cap = cv.VideoCapture(-1) # -1 means use first available camera
            if not self.cap.isOpened:
                print "Warning: Failed to open camera using OpenCV"
                cv_enabled=False
                return

            # Pick the video resolution to capture at.
            # If requested resolution is too high, OpenCV uses next best.
            # (E.g., 10000x10000 will force highest camera resolution).
            self.cap.set(cv.cv.CV_CAP_PROP_FRAME_WIDTH,  resolution[0])
            self.cap.set(cv.cv.CV_CAP_PROP_FRAME_HEIGHT, resolution[1])

            # Warm up web cam for quick start later and to double check driver
            r, dummy = self.cap.read()
            if not r:
                print "Warning: Failed to read from camera using OpenCV"
                cv_enabled=False
                return

            print "Connecting to camera using opencv"

            # Print the capabilities of the connected camera
            w=self.cap.get(cv.cv.CV_CAP_PROP_FRAME_WIDTH)
            h=self.cap.get(cv.cv.CV_CAP_PROP_FRAME_HEIGHT)
            if w and h:
                print("Camera detected as %d x %d" % (w, h))

            # Measure actual FPS of camera
            import time
            frames=0
            start = time.time()
            while (time.time() - 1 < start):
                frames = frames + 1
                self.cap.read()
            end = time.time()
            fps = frames/(end-start)
            print("Camera is capturing at %.2f fps" % (fps))

    def reinit(self):
        '''Close and reopen the video device. 
        This is mainly for debugging video capture problems.
        '''
        
        self.cap.release()
        self.cap = cv.VideoCapture(-1)
        r = self.cap.grab()
        if r:
            self.cv_enabled=True
        else:
            self.cv_enabled=False

    def set_rotate(self, camera_rotate):
        self.rotate = camera_rotate

    def get_rotate(self):
        return self.rotate

    def has_preview(self):
        return True 

    def take_preview(self, filename=tmp_dir + "preview.jpg"):
        self.take_picture(filename)

    def get_preview_array(self, max_size=None):
        """Get a quick preview from the camera and return it as a 2D array
        suitable for quick display using pygame.surfarray.blit_array().

        If a maximum size -- (w,h) -- is passed in, the returned image
        will be quickly decimated using numpy to be at most that large.
        """

        global cv_enabled
        if not cv_enabled:
            cv_enabled=True
            self.__init__()     # Try again to open the camera (e.g, just plugged in)
            if not cv_enabled:  # Still failed?
                raise CameraException("OpenCV: No camera found!")
            
        # Grab a camera frame
        r, f = self.cap.read()

        if not r:
            # We will never get here since OpenCV 2.4.9.1 is buggy
            # and never returns error codes once a webcam has been opened.
            # This is very annoying.
            cv_enabled=False
            raise CameraException("Error capturing frame using OpenCV!")

        # Optionally reduce frame size by decimation (nearest neighbor)
        if max_size:
            (max_w, max_h) = map(int, max_size)
            (    h,     w) = ( len(f), len(f[0]) ) # Note OpenCV swaps rows and columns
            w_factor = (w/max_w) + (1 if (w%max_w) else 0)
            h_factor = (h/max_h) + (1 if (h%max_h) else 0)
            scaling_factor = max( (w_factor, h_factor) )
            f=f[::scaling_factor, ::scaling_factor]

        # Convert from OpenCV format to Surfarray
        f=cv.cvtColor(f,cv.COLOR_BGR2RGB)
        f=numpy.rot90(f)        # OpenCV swaps rows and columns

        return f

    def get_preview_pygame_surface(self, max_size=None):
        """Get a quick preview from the camera and return it as a Pygame
        Surface suitable for transformation and display using GUI.py's
        surface_list.
        """
        f = self.get_preview_array(max_size)
        ( w,  h) = ( len(f), len(f[0]) )
        s=pygame.surfarray.make_surface(f)

        return s


    def take_picture(self, filename=tmp_dir+"picture.jpg"):
        global cv_enabled
        if cv_enabled:
            r, frame = self.cap.read()
            if not r:
                cv_enabled=False
                raise CameraException("Error capturing frame using OpenCV!")
            if self.rotate:     # Is camera on its side?
                frame=numpy.rot90(frame)
            cv.imwrite(filename, frame)
            return filename
        else:
            raise CameraException("OpenCV not available!")

    def set_idle(self):
        pass


class Camera_gPhoto:
    """Camera class providing functionality to take pictures using gPhoto 2"""

    def __init__(self, resolution=(10000,10000), camera_rotate=False):
        self.resolution = resolution # XXX Not used for gphoto?
        self.rotate = camera_rotate  # XXX Not yet implemented for gphoto.

        # Print the capabilities of the connected camera
        try:
            if gphoto2cffi_enabled:
                print "Connecting to camera using gphoto2cffi"
                self.cap = gp.Camera()
            elif piggyphoto_enabled:
                print "Connecting to camera using piggyphoto"
                self.cap = gp.camera()
                print(self.cap.abilities)
            else:
                print "Connecting to camera using command line gphoto2"
                print(self.call_gphoto("-a"))
        except CameraException as e:
            print('Warning: Listing camera capabilities failed (' + e.message + ')')
        except gpExcept as e:
            print('Warning: Listing camera capabilities failed (' + e.message + ')')

    def reinit(self):
        "Not needed for gphoto."
        return

    def call_gphoto(self, action, filename="/dev/null"):
        '''Run a gphoto2 command as a subprocess. 

        action is in the form of a valid command line argument, e.g.,
        '-a' or '--set-config capture=0'.

        filename is the name of the JPG file written to by --capture and --preview.

        '''
        # Try to run the command
        try:
            cmd = "gphoto2 --force-overwrite --quiet " + action + " --filename " + filename
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            if "ERROR" in output:
                raise subprocess.CalledProcessError(returncode=0, cmd=cmd, output=output)
        except subprocess.CalledProcessError as e:
            if "EOS Capture failed: 2019" in e.output or "Perhaps no focus" in e.output:
                raise CameraException("Can't focus!\nMove a little bit!", True)
            elif "No camera found" in e.output:
                raise CameraException("No (supported) camera detected!", False)
            elif "command not found" in e.output:
                raise CameraException("gPhoto2 not found!", False)
            else:
                raise CameraException("Unknown error!\n" + '\n'.join(e.output.split('\n')[1:3]), False)
        return output

    def set_rotate(self, camera_rotate):
        '''Force rotation of camera. Currently EXIF Orientation is always ignored.'''
        self.rotate = camera_rotate

    def get_rotate(self):
        return self.rotate

    def has_preview(self):
        return True

    def take_preview(self, filename=tmp_dir+"preview.jpg"):
        if gphoto2cffi_enabled:
            self._save_picture(filename, self.cap.get_preview())
        elif piggyphoto_enabled:
            self.cap.capture_preview(filename)	
        else:
            self.call_gphoto("--capture-preview", filename)

    def get_preview_array(self, max_size=None):
        """Get a quick preview from the camera and return it as a 2D array
        suitable for quick display using pygame.surfarray.blit_array().

        If a maximum size -- (w,h) -- is passed in, the returned image
        will be quickly decimated using numpy to be at most that large.
        """
        if gphoto2cffi_enabled:
            # Cffi can return the preview as a string. Yay!
            import StringIO   # Ugh. PIL wants stdio methods. (Maybe use scipy?)
            jpeg= StringIO.StringIO(self.cap.get_preview())
            f=numpy.array(Image.open(jpeg))

        elif piggyphoto_enabled:
            # Piggyphoto requires saving previews on filesystem! Yuck.
            # Probably should try a stringio hack, like for CFFI, above.
            piggy_preview = tmp_dir + "photobooth_piggy_preview.jpg"
            self.take_preview(piggy_preview)
            f=Image.open(piggy_preview)
            if self.rotate:     # Is camera on its side?
                f=f.transpose(Image.ROTATE_90)
            f=numpy.array(f)
        else:
            filename = "photobooth_cmdline_preview.jpg"
            cmdline_preview = tmp_dir + filename
            thumb_preview = tmp_dir + "thumb_" + filename
            self.take_preview(cmdline_preview)
            try:
                f=Image.open(thumb_preview)
                f=numpy.array(f)
            except IOError:
                # Gphoto always prepends "thumb_" even if --filename
                # is specified. This seems likely to go away as it
                # makes little sense. Let's be future-proof.
                try:
                    f=Image.open(cmdline_preview)
                    f=numpy.array(f)
                except Exception: 
                    raise CameraException("No preview supported!")

        # Optionally reduce frame size by decimation (nearest neighbor)
        if max_size:
            (max_w, max_h) = map(int, max_size)
            (    w,     h) = ( len(f), len(f[0]) )
            w_factor = (w/max_w) + (1 if (w%max_w) else 0)
            h_factor = (h/max_h) + (1 if (h%max_h) else 0)
            scaling_factor = max( (w_factor, h_factor) )
            f=f[::scaling_factor, ::scaling_factor]
        return f


    def get_preview_pygame_surface(self, max_size=None):
        """Get a quick preview from the camera and return it as a Pygame
        Surface suitable for transformation and display using GUI.py's
        surface_list.
        """
        f = self.get_preview_array(max_size)
        ( w,  h) = ( len(f), len(f[0]) )
        s=pygame.surfarray.make_surface(f)

        return s

    def take_picture(self, filename=tmp_dir + "picture.jpg"):
        if gphoto2cffi_enabled:
            self._save_picture(filename, self.cap.capture())
        elif piggyphoto_enabled:
            self.cap.capture_image(filename)
        else:
            self.call_gphoto("--capture-image-and-download", filename)
        if self.rotate:         # Is camera on its side?
            f=Image.open(filename)
            f=f.transpose(Image.ROTATE_90)
            f.save(filename)
        return filename

    def _save_picture(self, filename, data):
        f = open(filename, 'wb')
        f.write(data)
        f.close()

    def set_idle(self):
        if gphoto2cffi_enabled:
            if 'viewfinder' in self.cap._get_config()['actions']:
                self.cap._get_config()['actions']['viewfinder'].set(False)
            else:
                pass
        elif piggyphoto_enabled:
            pass
            # This doesn't work...
            #self.cap.config.main.actions.viewfinder.value = 0
