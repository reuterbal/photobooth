#!/usr/bin/env python
# Created by br@re-web.eu, 2015

import subprocess

try:
    import cv2 as cv
    cv_enabled = True
except ImportError:
    cv_enabled = False

class CameraException(Exception):
    """Custom exception class to handle camera class errors"""
    def __init__(self, message, recoverable=False):
        self.message = message
        self.recoverable = recoverable


class Camera_cv:
    def __init__(self, picture_size):
        if cv_enabled:
            self.cap = cv.VideoCapture(0)
            self.cap.set(3, picture_size[0])
            self.cap.set(4, picture_size[1])

    def take_picture(self, filename="/tmp/picture.jpg"):
        if cv_enabled:
            r, frame = self.cap.read()
            cv.imwrite(filename, frame)
            return filename
        else:
            raise CameraException("OpenCV not available!")


class Camera_gPhoto:
    """Camera class providing functionality to take pictures using gPhoto 2"""

    def __init__(self, picture_size):
        self.picture_size = picture_size
        # Print the capabilities of the connected camera
        try:
            print(self.call_gphoto("-a", "/dev/null"))
        except:
            print("Warning: Can't list camera capabilities. Do you have gPhoto2 installed?")

    def call_gphoto(self, action, filename):
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

    def take_picture(self, filename="/tmp/picture.jpg"):
        self.call_gphoto("--capture-image-and-download", filename)
        return filename
