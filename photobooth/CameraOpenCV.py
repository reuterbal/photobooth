#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from Camera import Camera

from PIL import Image
import cv2

class CameraOpenCV(Camera):

    def __init__(self):

        super().__init__()

        self.hasPreview = True
        self.hasIdle = False

        self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            raise RuntimeError('Camera could not be opened')


    def getPreview(self):

        return self.getPicture()


    def getPicture(self):
        
        status, frame = self._cap.read()
        if not status:
            raise RuntimeError('Failed to capture picture')

        # OpenCV yields frames in BGR format, conversion to RGB necessary.
        # (See https://stackoverflow.com/a/32270308)
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

