#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from time import time, sleep, localtime, strftime

from PIL import Image, ImageOps

from PictureList import PictureList
from PictureDimensions import PictureDimensions

import gui

class Photobooth:

    def __init__(self, config, camera):

        picture_basename = strftime(config.get('Picture', 'basename'), localtime())

        self._cap = camera
        self._pic_dims = PictureDimensions(config, self._cap.getPicture().size)
        self._pic_list = PictureList(picture_basename)

        self._greeter_time = config.getInt('Photobooth', 'greeter_time')
        self._countdown_time = config.getInt('Photobooth', 'countdown_time')
        self._display_time = config.getInt('Photobooth', 'display_time')

        if ( config.getBool('Photobooth', 'show_preview') 
            and self._cap.hasPreview ):
            self._show_counter = self.showCounterPreview
        else:
            self._show_counter = self.showCounterNoPreview

        self._get_next_filename = self._pic_list.getNext


    @property
    def getNextFilename(self):

        return self._get_next_filename


    @property
    def showCounter(self):

        return self._show_counter


    @property
    def greeterTime(self):

        return self._greeter_time


    @property
    def countdownTime(self):

        return self._countdown_time


    @property
    def displayTime(self):

        return self._display_time


    def run(self, send, recv):

        self._send = send
        self.setCameraIdle()
        self._send.send(gui.IdleState())

        while True:
            try:
                event = recv.recv()
                if str(event) != 'triggered':
                    print('Unknown event received: ' + str(event))
                    raise RuntimeError('Unknown event received', str(event))
            except EOFError:
                return 1
            else:
                try:
                    self.trigger()
                except RuntimeError as e:
                    print('Camera error: ' + str(e))
                    self._send.send( gui.ErrorState('Camera error', str(e)) )
                    event = recv.recv()
                    if str(event) == 'cancel':
                        return 1
                    elif str(event) == 'ack':
                        pass
                    else:
                        print('Unknown event received: ' + str(event))
                        raise RuntimeError('Unknown event received', str(event))

        return 0
        

    def setCameraActive(self):

        self._cap.setActive()
        

    def setCameraIdle(self):

        if self._cap.hasIdle:
            self._cap.setIdle()


    def showCounterPreview(self):

        tic, toc = time(), 0

        while toc < self.countdownTime:
            self._send.send( gui.PreviewState(
                message = str(self.countdownTime - int(toc)), 
                picture = ImageOps.mirror(self._cap.getPreview()) ) )
            toc = time() - tic


    def showCounterNoPreview(self):

        for i in range(self.countdownTime):
            self._send.send( gui.PreviewState(
                message = str(i),
                picture = Image.new('RGB', (1,1), 'white') ) )
            sleep(1)


    def showPose(self):

        self._send.send( gui.PoseState() )


    def captureSinglePicture(self):

        self.showCounter()
        self.showPose()
        return self._cap.getPicture()


    def assemblePictures(self, pictures):

        output_image = Image.new('RGB', self._pic_dims.outputSize, (255, 255, 255))

        for i in range(self._pic_dims.totalNumPictures):
            output_image.paste(pictures[i].resize(self._pic_dims.thumbnailSize), 
                self._pic_dims.thumbnailOffset[i])

        return output_image


    def capturePictures(self):

        pictures = [ self.captureSinglePicture() for _ in range(self._pic_dims.totalNumPictures) ]
        return self.assemblePictures(pictures)


    def trigger(self):

        self._send.send(gui.GreeterState())
        self.setCameraActive()

        sleep(self.greeterTime)

        img = self.capturePictures()
        img.save(self.getNextFilename(), 'JPEG')
        self._send.send(gui.PictureState(img))

        self.setCameraIdle()

        sleep(self.displayTime)

        self._send.send(gui.IdleState())

