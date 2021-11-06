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

from glob import glob


class PictureList:
    """A simple helper class.

    It provides the filenames for the assembled pictures and keeps count
    of taken and previously existing pictures.
    """

    def __init__(self, basename):
        """Initialize filenames to the given basename and search for
        existing files. Set the counter accordingly.
        """

        # Set basename and suffix
        self._basename = basename
        self.suffix = '.jpg'
        self.count_width = 5

        self.findExistingFiles()

    def findExistingFiles(self):
        """Count number of existing files matchin the given basename
        """
        # Find existing files
        count_pattern = '[0-9]' * self.count_width
        pictures = glob(self.basename + count_pattern + self.suffix)

        # Get number of latest file
        if len(pictures) == 0:
            self.counter = 0
        else:
            pictures.sort()
            last_picture = pictures[-1]
            self.counter = int(last_picture[
                -(self.count_width + len(self.suffix)):-len(self.suffix)])

        # Print initial infos
        logging.info('Number of last existing file: %d', self.counter)
        logging.info('Saving pictures as "%s%s.%s"', self.basename,
                     self.count_width * 'X', 'jpg')

    @property
    def basename(self):
        """Return the basename for the files"""
        return self._basename

    def getFilename(self, count, uuid=None, use_counter=True):
        """Return the file name for a given file number or a UUID"""
        if uuid:
            if use_counter:
                return self.basename + '-' + uuid + '_' + str(count) + self.suffix
            else:
                return self.basename + '-' + uuid + self.suffix
        return self.basename + str(count).zfill(self.count_width) + self.suffix

    def getLast(self):
        """Return the current filename"""
        return self.getFilename(self.counter)

    def getNext(self, uuid=None, use_counter=True):
        """Update counter and return the next filename"""
        self.counter += 1
        return self.getFilename(self.counter, uuid, use_counter)

    def resetCounter(self):
        self.counter = 0
