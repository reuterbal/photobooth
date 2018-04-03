#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class PictureDimensions:

    def __init__(self, config, capture_size):

        self._num_pictures = ( config.getInt('Picture', 'num_x') ,
                               config.getInt('Picture', 'num_y') )

        self._capture_size = capture_size

        self._output_size = ( config.getInt('Picture', 'size_x') ,
                              config.getInt('Picture', 'size_y') )

        self._min_distance = ( config.getInt('Picture', 'min_dist_x') ,
                               config.getInt('Picture', 'min_dist_y') )

        self.computeThumbnailDimensions()


    def computeThumbnailDimensions(self):

        resize_factor = min( ( (
            ( self.outputSize[i] - (self.numPictures[i] + 1) * self.minDistance[i] ) / 
            ( self.numPictures[i] * self.captureSize[i]) ) for i in range(2) ) )

        self._thumb_size = tuple( int(self.captureSize[i] * resize_factor)
            for i in range(2) )

        output_picture_dist = tuple( ( self.outputSize[i] - self.numPictures[i] * 
                self.thumbnailSize[i] ) // (self.numPictures[i] + 1)
            for i in range(2) )

        self._thumb_offsets = []
        for i in range(self.totalNumPictures):
            pos = (i % self.numPictures[0], i // self.numPictures[0])
            self._thumb_offsets.append( tuple( 
                (pos[j] + 1) * output_picture_dist[j] +
                pos[j] * self.thumbnailSize[j] for j in range(2) ) )


    @property
    def numPictures(self):

        return self._num_pictures


    @property
    def totalNumPictures(self):

        return self._num_pictures[0] * self._num_pictures[1]

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
