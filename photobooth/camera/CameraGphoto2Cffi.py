#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Photobooth - a flexible photo booth software
# Copyright (C) 2018  Balthasar Reuter <photobooth at re - web dot eu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import io
import logging

from PIL import Image

import gphoto2cffi as gp

from .CameraInterface import CameraInterface


class CameraGphoto2Cffi(CameraInterface):

    def __init__(self):

        super().__init__()

        self.hasPreview = True
        self.hasIdle = True

        logging.info('Using gphoto2-cffi bindings')

        self._setupCamera()

    def cleanup(self):

        self._cap.config['imgsettings']['imageformat'].set(self._imgfmt)
        self._cap.config['imgsettings']['imageformatsd'].set(self._imgfmtsd)
        # self._cap.config['settings']['autopoweroff'].set(self._autopoweroff)

    def _setupCamera(self):

        self._cap = gp.Camera()
        logging.info('Supported operations: %s',
                     self._cap.supported_operations)

        # make sure camera format is not set to raw
        imgfmt = 'Large Fine JPEG'
        self._imgfmt = self._cap.config['imgsettings']['imageformat'].value
        if 'raw' in self._imgfmt.lower():
            self._cap.config['imgsettings']['imageformat'].set(imgfmt)
        self._imgfmtsd = self._cap.config['imgsettings']['imageformatsd'].value
        if 'raw' in self._imgfmtsd.lower():
            self._cap.config['imgsettings']['imageformatsd'].set(imgfmt)

        # make sure autopoweroff is disabled
        # this doesn't seem to work
        # self._autopoweroff = int(
        #                   self._cap.config['settings']['autopoweroff'].value)
        #  if self._autopoweroff > 0:
        #      self._cap.config['settings']['autopoweroff'].set("0")

        # print current config
        self._printConfig(self._cap.config)

    @staticmethod
    def _configTreeToText(config, indent=0):

        config_txt = ''

        for k, v in config.items():
            config_txt += indent * ' '
            config_txt += k + ': '

            if hasattr(v, '__len__') and len(v) > 1:
                config_txt += '\n'
                config_txt += CameraGphoto2Cffi._configTreeToText(v,
                                                                  indent + 4)
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
        self._cap._get_config()['settings']['output'].set('PC')

    def setIdle(self):

        self._cap._get_config()['actions']['viewfinder'].set(False)
        self._cap._get_config()['settings']['output'].set('Off')

    def getPreview(self):

        return Image.open(io.BytesIO(self._cap.get_preview()))

    def getPicture(self):

        return Image.open(io.BytesIO(self._cap.capture()))
