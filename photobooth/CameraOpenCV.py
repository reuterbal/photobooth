#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from Camera import Camera

import cv2

class CameraOpenCV(Camera):

    def __init__(self):

        super().__init__()

        self.hasPreview = True
        self.hasIdle = False

        self._cap = cv2.VideoCapture(-1)
        if not self._cap.isOpened():
            raise RuntimeError('Camera could not be opened')


    def getPreview(self):

        return self.getPicture()


    def getPicture(self):

        _, frame = self._cap.read()
        # OpenCV yields frames in BGR format, 
        # see https://stackoverflow.com/a/32270308
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

