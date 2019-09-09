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

from .WorkerTask import WorkerTask


class PictureSaver(WorkerTask):

    def __init__(self, basename):

        super().__init__()

        # Ensure directory exists
        dirname = os.path.dirname(basename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    def do(self, picture, filename):

        logging.info('Saving picture as %s', filename)
        with open(filename, 'wb') as f:
            f.write(picture.getbuffer())
