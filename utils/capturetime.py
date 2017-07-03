#!/usr/bin/python
# This program tests which gphoto2 interface has the fastest capture.

# Results on my Raspberry Pi3b with Canon PowerShot A510

# libgphoto2.so:  5s
# rtiacquire   :  7s
# gphoto2-cffi : 13s *
# piggyphoto   :  6s

# Oddly, these times don't change much if I shoot at low resolution.
# (gphoto2 --set-config /main/imgsettings/imagesize=3)
# So, I'm not sure what the bottleneck is. 

# * Note, I assume gphoto2-cffi works for some other cameras. But on my
# camera (Canon Powershot A510), it throws a CameraIO exception and
# sometimes causes my camera's firmware to lock up. To workaround it,
# I'm calling capture() with to_camera_storage=True. That makes it extra slow. 





from time import time

try:
    gp=None
    import ctypes
    class CameraFilePath(ctypes.Structure):
        _fields_ = [('name', (ctypes.c_char * 128)),
                    ('folder', (ctypes.c_char * 1024))]
    gp = ctypes.CDLL("libgphoto2.so")
    context=gp.gp_context_new()
    cam=ctypes.c_void_p()
    gp.gp_camera_new(ctypes.pointer(cam))

    gp.gp_camera_init(cam, context)
    cfile = ctypes.c_void_p()
    gp.gp_file_new(ctypes.pointer(cfile))
    cfilepath = CameraFilePath()

    t=time()
    gp.gp_camera_capture(cam, 0, ctypes.pointer(cfilepath), context)
    gp.gp_camera_file_get(cam, cfilepath.folder, cfilepath.name, 1, cfile, context)
    gp.gp_file_save(cfile, "/dev/shm/gphoto2.so.jpg")
    t=time()-t
    print ("gphoto2.so capture time: %f" % (t))
except:
    raise
finally:
    if gp: gp.gp_camera_exit(cam, context)


try:
    cap=None
    from rtiacquire import camera
    cap=camera.Camera()
    t=time()
    cap.capture_to_file("/dev/shm/rtiacquire")
    t=time()-t
    print ("RTIacquire capture time: %f" % (t))
except:
    pass
finally:
    if cap:  cap.release()    


try:
    import gphoto2cffi
    cap=gphoto2cffi.Camera()
    gphoto2cffi_buggy=True
    t=time()
    data = cap.capture(to_camera_storage=gphoto2cffi_buggy) # Work around bug  
    data.save("/dev/shm/gphoto2cffi.jpg")
    if gphoto2cffi_buggy:  data.remove()
    t=time()-t
    print ("gphoto2cffi capture time: %f" % (t))
except:
    raise
finally:
    cap=None

try:
    import piggyphoto
    import pygame
    cap=piggyphoto.camera()
    t=time()
    cap.capture_image("/dev/shm/piggy.jpg")
    t=time()-t
    print ("piggyphoto capture time: %f" % (t))
except:
    pass
finally:
    cap=None

