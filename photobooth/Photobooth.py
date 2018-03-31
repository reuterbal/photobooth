#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from Config import Config

from PictureList import PictureList

import Gui
from PyQt5Gui import PyQt5Gui

from CameraOpenCV import CameraOpenCV as Camera

from PIL import Image, ImageOps

from multiprocessing import Pipe, Process

from time import time, sleep, localtime, strftime


output_size = (1920, 1080)
min_distance = (10, 10)
# num_pictures = (2, 2)
pose_time = 2
picture_basename = strftime('%Y-%m-%d/photobooth', localtime())

class Photobooth:

    def __init__(self, config):

        self._cap = Camera()
        self._cfg = config

        if ( self._cfg.getBool('Photobooth', 'show_preview') 
            and self._cap.hasPreview ):
            self.showCounter = self.showCounterPreview
        else:
            self.showCounter = self.showCounterNoPreview

        self.numPictures = ( self._cfg.getInt('Photobooth', 'num_pictures_x') ,
                             self._cfg.getInt('Photobooth', 'num_pictures_y') )

    @property
    def getNextFilename(self):

        return self._get_next_filename


    @getNextFilename.setter
    def getNextFilename(self, func):

        if not callable(func):
            raise ValueError('getNextFilename must be callable')

        self._get_next_filename = func


    @property
    def showCounter(self):

        return self._show_counter


    @showCounter.setter
    def showCounter(self, func):

        if not callable(func):
            raise ValueError('showCounter must be callable')

        self._show_counter = func


    @property
    def numPictures(self):

        return self._num_pictures


    @numPictures.setter
    def numPictures(self, num_pictures):

        if len(num_pictures) != 2:
            raise ValueError('num_pictures must have two entries')

        self._num_pictures = num_pictures


    def run(self, send, recv):

        self._send = send

        while True:
            try:
                event = recv.recv()
            except EOFError:
                return 1
            else:
                try:
                    self.trigger()
                except RuntimeError as e:
                    print('Camera error: ' + str(e))
                    self._send.send( Gui.ErrorState('Camera error', str(e)) )

        return 0
        

    def setCameraActive(self):

        self._cap.setActive()
        

    def setCameraIdle(self):

        if self._cap.hasIdle:
            self._cap.setIdle()


    def showCounterPreview(self):

        tic, toc = time(), 0

        while toc < pose_time:
            self._send.send( Gui.PreviewState(
                message = str(pose_time - int(toc)), 
                picture = ImageOps.mirror(self._cap.getPreview()) ) )
            toc = time() - tic


    def showCounterNoPreview(self):

        for i in range(pose_time):
            self._send.send( Gui.PreviewState(str(i)) )
            sleep(1)


    def captureSinglePicture(self):

        self.showCounter()

        return self._cap.getPicture()


    def assemblePictures(self, pictures):

        # TODO: determine sizes only once
        picture_size = pictures[0].size

        resize_factor = min( ( (
            ( output_size[i] - (self.numPictures[i] + 1) * min_distance[i] ) / 
            ( self.numPictures[i] * picture_size[i]) ) for i in range(2) ) )

        output_picture_size = tuple( int(picture_size[i] * resize_factor)
            for i in range(2) )
        output_picture_dist = tuple( ( output_size[i] - self.numPictures[i] * 
                output_picture_size[i] ) // (self.numPictures[i] + 1)
            for i in range(2) )

        output_image = Image.new('RGB', output_size, (255, 255, 255))

        idx = 0
        for img in pictures:
            pos = (idx % self.numPictures[0], idx // self.numPictures[0])
            img = img.resize(output_picture_size)
            offset = tuple( (pos[i] + 1) * output_picture_dist[i] +
                pos[i] * output_picture_size[i] for i in range(2) )
            output_image.paste(img, offset)
            idx += 1

        return output_image


    def capturePictures(self):

        pictures = [self.captureSinglePicture() 
            for i in range(2) for _ in range(self.numPictures[i])]
        return self.assemblePictures(pictures)


    def trigger(self):

        self._send.send(Gui.PoseState())
        self.setCameraActive()

        sleep(2)

        img = self.capturePictures()
        img.save(self.getNextFilename(), 'JPEG')
        self._send.send(Gui.PictureState(img))

        self.setCameraIdle()

        sleep(5)

        self._send.send(Gui.IdleState())


def main_photobooth(config, send, recv):

    picture_list = PictureList(picture_basename)

    photobooth = Photobooth(config)
    photobooth.getNextFilename = picture_list.getNext

    return photobooth.run(send, recv)


def main(argv):

    config = Config('photobooth.cfg')

    event_recv, event_send = Pipe(duplex=False)
    gui_recv, gui_send = Pipe(duplex=False)

    photobooth = Process(target=main_photobooth, args=(config, gui_send, event_recv), daemon=True)
    photobooth.start()

    gui = PyQt5Gui(argv, config)
    return gui.run(event_send, gui_recv)
