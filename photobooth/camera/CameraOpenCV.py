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

import logging

from PIL import Image

import cv2

from .CameraInterface import CameraInterface


class CameraOpenCV(CameraInterface):

    def __init__(self):

        super().__init__()

        self.hasPreview = True
        self.hasIdle = True

        logging.info('Using OpenCV')

        self._cap = cv2.VideoCapture()

    def setActive(self):

        if not self._cap.isOpened():
            self._cap.open(0)
            if not self._cap.isOpened():
                raise RuntimeError('Camera could not be opened')

    def setIdle(self):

        if self._cap.isOpened():
            self._cap.release()

    def getPreview(self):

        return self.getPicture()

    def getPicture(self):

        self.setActive()
        status, frame = self._cap.read()
        if not status:
            raise RuntimeError('Failed to capture picture')

        # OpenCV yields frames in BGR format, conversion to RGB necessary.
        # (See https://stackoverflow.com/a/32270308)
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
