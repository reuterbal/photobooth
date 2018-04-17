#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io, logging

from PIL import Image

import gphoto2cffi as gp

from . import Camera


class CameraGphoto2Cffi(Camera):

    def __init__(self):

        super().__init__()

        self.hasPreview = True
        self.hasIdle = True

        # Avoid output cluttered
        logging.basicConfig(
            format='%(levelname)s: %(name)s: %(message)s', 
            level=logging.CRITICAL)

        self._setupCamera()


    def _setupCamera(self):

        self._cap = gp.Camera()
        print(self._cap.supported_operations)

        if 'raw' in self._cap.config['imgsettings']['imageformat'].value.lower():
            raise RuntimeError('Camera file format is set to RAW')


    def setActive(self):

        self._cap._get_config()['actions']['viewfinder'].set(True)


    def setIdle(self):

        self._cap._get_config()['actions']['viewfinder'].set(False)


    def getPreview(self):

        return Image.open(io.BytesIO(self._cap.get_preview()))


    def getPicture(self):
        
        return Image.open(io.BytesIO(self._cap.capture()))

