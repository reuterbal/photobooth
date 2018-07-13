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
import os
import subprocess

from PIL import Image

from .CameraInterface import CameraInterface


class CameraGphoto2CommandLine(CameraInterface):

    def __init__(self):

        super().__init__()

        self.hasPreview = False
        self.hasIdle = False

        logging.info('Using gphoto2 via command line')

        if os.access('/dev/shm', os.W_OK):
            logging.debug('Storing temp files to "/dev/shm/photobooth.jpg"')
            self._tmp_filename = '/dev/shm/photobooth.jpg'
        else:
            logging.debug('Storing temp files to "/tmp/photobooth.jpg"')
            self._tmp_filename = '/tmp/photobooth.jpg'

        self.setActive()

    def setActive(self):

        self._callGphoto('-a', '/dev/null')

    def getPicture(self):

        self._callGphoto('--capture-image-and-download', self._tmp_filename)
        return Image.open(self._tmp_filename)

    def _callGphoto(self, action, filename):

        cmd = 'gphoto2 --force-overwrite --quiet {} --filename {}'
        return subprocess.check_output(cmd.format(action, filename),
                                       shell=True, stderr=subprocess.STDOUT)
