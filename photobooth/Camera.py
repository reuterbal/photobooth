#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class Camera:

    def __init__(self):

        self.hasPreview = False
        self.hasIdle = False

    @property
    def hasPreview(self):

        return self._has_preview


    @hasPreview.setter
    def hasPreview(self, value):

        if not isinstance(value, bool):
            raise ValueError('Expected bool')

        self._has_preview = value

    @property
    def hasIdle(self):

        return self._has_idle
        

    @hasIdle.setter
    def hasIdle(self, value):

        if not isinstance(value, bool):
            raise ValueError('Expected bool')

        self._has_idle = value


    def setActive(self):

        if not self.hasIdle:
            pass
        else:
            raise NotImplementedError()


    def setIdle(self):

        if not self.hasIdle:
            raise RuntimeError('Camera does not have idle functionality')

        raise NotImplementedError()


    def getPreview(self):

        if not self.hasPreview:
            raise RuntimeError('Camera does not have preview functionality')

        raise NotImplementedError()


    def getPicture(self):

        raise NotImplementedError()


    def setIdle(self):

        if not self.hasIdle:
            raise RuntimeError('Camera does not support idle state')

        raise NotImplementedError()