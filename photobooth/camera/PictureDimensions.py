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


class PictureDimensions:

    def __init__(self, config, capture_size):

        self._num_pictures = (config.getInt('Picture', 'num_x'),
                              config.getInt('Picture', 'num_y'))

        self._capture_size = capture_size

        self._output_size = (config.getInt('Picture', 'size_x'),
                             config.getInt('Picture', 'size_y'))

        self._inner_distance = (config.getInt('Picture', 'inner_dist_x'),
                                config.getInt('Picture', 'inner_dist_y'))
        self._outer_distance = (config.getInt('Picture', 'outer_dist_x'),
                                config.getInt('Picture', 'outer_dist_y'))

        self._skip = [i for i in config.getIntList('Picture', 'skip')
                      if 1 <= i and
                      i <= self._num_pictures[0] * self._num_pictures[1]]
        
        logging.info('_skip: "{}"'.format(self._skip))

        self.computeThumbnailDimensions()

        self.computePreviewDimensions(config)

    def _computeResizeFactor(self, coord, inner_size):

        return ((inner_size - (self.numPictures[coord] + 1) *
                 self.innerDistance[coord]) /
                (self.numPictures[coord] * self.captureSize[coord]))

    def _computeThumbOffset(self, coord, inner_size):

        return (inner_size - self.numPictures[coord] *
                self.thumbnailSize[coord]) // (self.numPictures[coord] + 1)

    def computeThumbnailDimensions(self):

        border = tuple(self.outerDistance[i] - self.innerDistance[i]
                       for i in range(2))
        inner_size = tuple(self.outputSize[i] - 2 * border[i]
                           for i in range(2))

        resize_factor = min(self._computeResizeFactor(i, inner_size[i])
                            for i in range(2))
        self._thumb_size = tuple(int(self.captureSize[i] * resize_factor)
                                 for i in range(2))

        thumb_dist = tuple(self._computeThumbOffset(i, inner_size[i])
                           for i in range(2))

        self._thumbs = [i for i in range(self.numPictures[0] * self.numPictures[1]) #websta added self._
                  if i + 1 not in self._skip]

        self._thumb_offsets = []
        #websta changedfrom thumbs
        if (self.numPictures[0] * self.numPictures[1]) > 1: #for mor than one picture
            for i in range(self.numPictures[0] * self.numPictures[1]):
                pos = (i % self.numPictures[0], i // self.numPictures[0])
                #self._thumb_offsets.append(tuple(border[j] + (pos[j] + 1) * thumb_dist[j] + pos[j] * self.thumbnailSize[j] for j in range(2)))
                # websta: changed to calculate from center of image so the spacing is horizontally and vertically equal
                thumb_offs = []
                for j in range(2):
                    if pos[j] < 1 :
                        thumb_offs.append(self.outputSize[j]//2 - self.thumbnailSize[j] - (thumb_dist[1] // 2))
                    else :
                        thumb_offs.append(self.outputSize[j]//2 +  (thumb_dist[1] // 2))

                self._thumb_offsets.append(tuple(thumb_offs[j] 
                                             for j in range(2)))
        else: # if just one picture center the picture
             self._thumb_offsets.append(tuple((self.outputSize[j]//2 - self.thumbnailSize[j]//2)
                                                                 for j in range(2)))

        logging.debug(('Assembled picture will contain {} ({}x{}) pictures '
                       'in positions {}').format(self.totalNumPictures,
                                                 self.numPictures[0],
                                                 self.numPictures[1], self._thumbs))

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

    @property # added property thumbslocation
    def thumbsLocation(self):

        return self._thumbs

    @property
    def totalNumPictures(self):

        return max(self._num_pictures[0] * self._num_pictures[1] -
                   len(self._skip), 1)

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
    def innerDistance(self):

        return self._inner_distance

    @property
    def outerDistance(self):

        return self._outer_distance

    @property
    def thumbnailSize(self):

        return self._thumb_size

    @property
    def thumbnailOffset(self):

        return self._thumb_offsets

    @property
    def previewSize(self):

        return self._preview_size
