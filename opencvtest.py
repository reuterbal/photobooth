#!/usr/bin/python

# What the heck. My Logitech QuickCam gets slower on every read() when
# I use OpenCV 2.4.9 but works fine with other V4L2 apps. If I release
# and reopen the camera, it becomes fast again.

# This program just prints out FPS every second. This is what the
# output looks like on my Raspberry Pi 3B and Logitech QuickCam:
#
#####################################################################
# ./opencvtest.py                                                   #
# Camera detected as 640 x 480                                      #
# First frame took 3.501s to grab                                   #
# After 0016 frames, 0001 seconds: Camera is capturing at 14.26 fps #
# After 0031 frames, 0002 seconds: Camera is capturing at 14.20 fps #
# After 0044 frames, 0003 seconds: Camera is capturing at 12.69 fps #
# After 0056 frames, 0004 seconds: Camera is capturing at 11.37 fps #
# After 0067 frames, 0005 seconds: Camera is capturing at 10.11 fps #
# After 0077 frames, 0006 seconds: Camera is capturing at 9.47 fps  #
# After 0086 frames, 0007 seconds: Camera is capturing at 8.79 fps  #
# After 0095 frames, 0008 seconds: Camera is capturing at 8.27 fps  #
# After 0103 frames, 0009 seconds: Camera is capturing at 7.81 fps  #
# ...                                                               #
# After 0199 frames, 0025 seconds: Camera is capturing at 4.88 fps  #
# After 0204 frames, 0026 seconds: Camera is capturing at 4.73 fps  #
# ...                                                               #
# After 0298 frames, 0050 seconds: Camera is capturing at 3.47 fps  #
# After 0302 frames, 0051 seconds: Camera is capturing at 3.47 fps  #
# ...                                                               #
# After 0399 frames, 0083 seconds: Camera is capturing at 2.75 fps  #
# After 0402 frames, 0084 seconds: Camera is capturing at 2.67 fps  #
# ...                                                               #
# After 0498 frames, 0153 seconds: Camera is capturing at 0.50 fps  #
# After 0500 frames, 0156 seconds: Camera is capturing at 0.99 fps  #
# After 0502 frames, 0157 seconds: Camera is capturing at 1.33 fps  #
# After 0504 frames, 0159 seconds: Camera is capturing at 0.99 fps  #
# After 0506 frames, 0166 seconds: Camera is capturing at 0.30 fps  #
#####################################################################

import time
import cv2

# Open the first available camera
cap = cv2.VideoCapture(-1)
if not cap.isOpened:
    print "Warning: Failed to open camera using OpenCV"
    exit
    
# Print the capabilities of the connected camera
w=cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
h=cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
if w and h:
    print("Camera detected as %d x %d" % (w, h))

# The first read always takes a long time. No idea why.
start = time.time()
cap.grab()
end = time.time()
print("First frame took %0.3fs to grab" % (end - start) )

overall_start=time.time()
total_frames=1
while True:
        # Measure actual FPS of camera
        frames=0
        start = time.time()
        while (time.time() - 1 < start):
            frames = frames + 1
            cap.grab()          # <== This is where the bottleneck is
        end = time.time()
        fps = frames/(end-start)
        total_frames=total_frames+frames
        print("After %04d frames, %04d seconds: Camera is capturing at %.2f fps" % (total_frames, int(time.time()-overall_start), fps))

        
