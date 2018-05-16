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

        logging.info('Using gphoto2-cffi bindings')

        self._setupCamera()


    def _setupCamera(self):

        self._cap = gp.Camera()
        logging.info('Supported operations: %s', self._cap.supported_operations)

        if 'raw' in self._cap.config['imgsettings']['imageformat'].value.lower():
            raise RuntimeError('Camera file format is set to RAW')

        self._printConfig(self._cap.config)


    @staticmethod
    def _configTreeToText(config, indent=0):

        config_txt = ''

        for k, v in config.items():
            config_txt += indent * ' '
            config_txt += k + ': '

            if hasattr(v, '__len__') and len(v) > 1:
                config_txt += '\n'
                config_txt += CameraGphoto2Cffi._configTreeToText(v, indent + 4)
            else:
                config_txt += str(v) + '\n'

        return config_txt


    @staticmethod
    def _printConfig(config):
        config_txt = 'Camera configuration:\n'
        config_txt += CameraGphoto2Cffi._configTreeToText(config)
        logging.info(config_txt)


    def setActive(self):

        self._cap._get_config()['actions']['viewfinder'].set(True)


    def setIdle(self):

        self._cap._get_config()['actions']['viewfinder'].set(False)


    def getPreview(self):

        return Image.open(io.BytesIO(self._cap.get_preview()))


    def getPicture(self):
        
        return Image.open(io.BytesIO(self._cap.capture()))

