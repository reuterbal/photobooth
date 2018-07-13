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
from colorsys import hsv_to_rgb

from PIL import Image

from .CameraInterface import CameraInterface


class CameraDummy(CameraInterface):

    def __init__(self):

        super().__init__()

        self.hasPreview = True
        self.hasIdle = False
        self._size = (1920, 1280)

        self._hue = 0

        logging.info('Using CameraDummy')

    def getPreview(self):

        return self.getPicture()

    def getPicture(self):

        self._hue = (self._hue + 1) % 360
        r, g, b = hsv_to_rgb(self._hue / 360, .2, .9)
        return Image.new('RGB', self._size, (int(r * 255), int(g * 255),
                                             int(b * 255)))
