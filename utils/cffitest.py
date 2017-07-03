#!/usr/bin/python

# Testing gphoto2cffi fps

import gphoto2cffi as gp
import pygame
from PIL  import Image
import StringIO   # Ugh. PIL wants stdio methods. (Maybe use scipy?)

pygame.init()
pygame.display.set_caption('CFFItest')
screen=pygame.display.set_mode((0,0), pygame.FULLSCREEN)            
i = pygame.display.Info()
size = (i.current_w, i.current_h)
screen.fill((0,0,0))
pygame.display.update()


cap=gp.Camera()

from time import time
t=time()

frames=100
for i in range(frames):
    jpegstring=cap.get_preview()
    jpegio = StringIO.StringIO(jpegstring)
    image=pygame.image.load(jpegio)
    screen.blit(image, (0,0))
    pygame.display.update()
print ("\nFPS: %f\n" % (frames/(time()-t)))


