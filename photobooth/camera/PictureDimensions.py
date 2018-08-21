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


class PictureDimensions:

    def __init__(self, config, capture_size):

        self._num_pictures = (config.getInt('Picture', 'num_x'),
                              config.getInt('Picture', 'num_y'))

        self._capture_size = capture_size

        self._output_size = (config.getInt('Picture', 'size_x'),
                             config.getInt('Picture', 'size_y'))

        self._min_distance = (config.getInt('Picture', 'min_dist_x'),
                              config.getInt('Picture', 'min_dist_y'))

        self._skip_last = config.getBool('Picture', 'skip_last')

        self.computeThumbnailDimensions()

        self.computePreviewDimensions(config)

    def computeThumbnailDimensions(self):

        resize_factor = min((((self.outputSize[i] - (self.numPictures[i] + 1) *
                               self.minDistance[i]) /
                              (self.numPictures[i] * self.captureSize[i]))
                             for i in range(2)))

        self._thumb_size = tuple(int(self.captureSize[i] * resize_factor)
                                 for i in range(2))

        thumb_dist = tuple((self.outputSize[i] - self.numPictures[i] *
                            self.thumbnailSize[i]) // (self.numPictures[i] + 1)
                           for i in range(2))

        self._thumb_offsets = []
        for i in range(self.totalNumPictures):
            pos = (i % self.numPictures[0], i // self.numPictures[0])
            self._thumb_offsets.append(tuple((pos[j] + 1) * thumb_dist[j] +
                                             pos[j] * self.thumbnailSize[j]
                                             for j in range(2)))

    def computePreviewDimensions(self, config):

        gui_size = (config.getInt('Gui', 'width'),
                    config.getInt('Gui', 'height'))

        resize_factor = min(min((gui_size[i] / self.captureSize[i]
                                 for i in range(2))), 1)

        self._preview_size = tuple(int(self.captureSize[i] * resize_factor)
                                   for i in range(2))

    @property
    def numPictures(self):

        return self._num_pictures

    @property
    def totalNumPictures(self):

        return max(self._num_pictures[0] * self._num_pictures[1] -
                   int(self._skip_last), 1)

    @property
    def skipLast(self):

        return self._skip_last

    @property
    def captureSize(self):

        return self._capture_size

    @property
    def outputSize(self):

        return self._output_size

    @property
    def minDistance(self):

        return self._min_distance

    @property
    def thumbnailSize(self):

        return self._thumb_size

    @property
    def thumbnailOffset(self):

        return self._thumb_offsets

    @property
    def previewSize(self):

        return self._preview_size
