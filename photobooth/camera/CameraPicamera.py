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

from picamera import PiCamera

from .CameraInterface import CameraInterface


class CameraPicamera(CameraInterface):

    def __init__(self):

        super().__init__()

        self.hasPreview = True
        self.hasIdle = True

        logging.info('Using PiCamera')

        self._cap = None

        self.setActive()
        self._preview_resolution = (self._cap.resolution[0] // 2,
                                    self._cap.resolution[1] // 2)
        self.setIdle()

    def setActive(self):

        if self._cap is None or self._cap.closed:
            self._cap = PiCamera()

    def setIdle(self):

        if self._cap is not None and not self._cap.closed:
            self._cap.close()
            self._cap = None

    def getPreview(self):

        self.setActive()
        stream = io.BytesIO()
        self._cap.capture(stream, format='jpeg', use_video_port=True,
                          resize=self._preview_resolution)
        stream.seek(0)
        return Image.open(stream)

    def getPicture(self):

        self.setActive()
        stream = io.BytesIO()
        self._cap.capture(stream, format='jpeg', resize=None)
        stream.seek(0)
        return Image.open(stream)
