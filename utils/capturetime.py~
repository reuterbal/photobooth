#!/usr/bin/python
# There are several different python interfaces to gphoto2.
# All of them have drawbacks. 

# This program tests which gphoto2 interface has the fastest preview code.

# On my Raspberry Pi3b with Canon Powershot A510
# gphoto2.so    : 22 fps
# RTIacquire    : 19 fps
# gphoto2cffi   :  6 fps
# piggyphoto    : 21 fps

# It would appear that piggyphoto -- while I dislike that it cannot read
# directly to memory -- is the best python library available.

from time import time

frames=100

try:
    import ctypes
    gp = ctypes.CDLL("libgphoto2.so")
    context=gp.gp_context_new()
    cam=ctypes.c_void_p()
    gp.gp_camera_new(ctypes.pointer(cam))
    cfile = ctypes.c_void_p()
    gp.gp_file_new(ctypes.pointer(cfile))

    gp.gp_camera_init(cam, context)
    t=time()
    for i in range(frames):
        gp.gp_camera_capture_preview(cam, cfile, context)
    t=time()-t
    print ("gphoto2.so preview FPS: %f" % (frames/t))
    gp.gp_camera_exit(cam, context)
except:
    raise


try:
    from rtiacquire import camera 
    cap=camera.Camera()
    t=time()
    for i in range(frames):
        (data, length) = cap.preview()
    t=time()-t
    print ("RTIacquire preview FPS: %f" % (frames/t))
    cap.release()    
except:
    pass


try:
    import gphoto2cffi
    cap=gphoto2cffi.Camera()
    t=time()
    for i in range(frames):
        data = cap.get_preview()
    t=time()-t
    print ("gphoto2cffi preview FPS: %f" % (frames/t))
    cap=None
except:
    pass

try:
    import piggyphoto
    import pygame
    cap=piggyphoto.camera()
    t=time()
    for i in range(frames):
        # Note that piggyphoto has no way to access image in memory. 
        # Using /dev/shm/ is a workaround.
        cap.capture_preview("/dev/shm/piggy.jpg")
        f=open("/dev/shm/piggy.jpg", "r")
        data=f.read()
    t=time()-t
    print ("piggyphoto preview FPS: %f" % (frames/t))
except:
    pass


