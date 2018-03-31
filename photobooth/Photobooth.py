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
num_pictures = (2, 2)
pose_time = 2
picture_basename = strftime('%Y-%m-%d/photobooth', localtime())

class Photobooth:

    def __init__(self):

        self._cap = Camera()


    @property
    def getNextFilename(self):

        return self._get_next_filename

    @getNextFilename.setter
    def getNextFilename(self, func):

        if not callable(func):
            raise ValueError('getNextFilename must be callable')

        self._get_next_filename = func


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


    def showCounter(self):

        if self._cap.hasPreview:
            tic, toc = time(), 0

            while toc < pose_time:
                self._send.send( Gui.PreviewState(
                    message = str(pose_time - int(toc)), 
                    picture = ImageOps.mirror(self._cap.getPreview()) ) )
                toc = time() - tic
        else:
            for i in range(pose_time):
                self._send.send( Gui.PreviewState(str(i)) )
                sleep(1)


    def captureSinglePicture(self):

        self.showCounter()

        return self._cap.getPicture()


    def assemblePictures(self, pictures):

        picture_size = pictures[0].size

        resize_factor = min( ( (
            ( output_size[i] - (num_pictures[i] + 1) * min_distance[i] ) / 
            ( num_pictures[i] * picture_size[i]) ) for i in range(2) ) )

        output_picture_size = tuple( int(picture_size[i] * resize_factor)
            for i in range(2) )
        output_picture_dist = tuple( ( output_size[i] - num_pictures[i] * 
                output_picture_size[i] ) // (num_pictures[i] + 1)
            for i in range(2) )

        output_image = Image.new('RGB', output_size, (255, 255, 255))

        idx = 0
        for img in pictures:
            pos = (idx % num_pictures[0], idx // num_pictures[0])
            img = img.resize(output_picture_size)
            offset = tuple( (pos[i] + 1) * output_picture_dist[i] +
                pos[i] * output_picture_size[i] for i in range(2) )
            output_image.paste(img, offset)
            idx += 1

        return output_image


    def capturePictures(self):

        pictures = [self.captureSinglePicture() 
            for i in range(2) for _ in range(num_pictures[i])]
        return self.assemblePictures(pictures)


    def trigger(self):

        self._send.send(Gui.PoseState())

        sleep(2)

        img = self.capturePictures()
        img.save(self.getNextFilename(), 'JPEG')
        self._send.send(Gui.PictureState(img))

        sleep(5)

        self._send.send(Gui.IdleState())


def main_photobooth(send, recv):

    picture_list = PictureList(picture_basename)

    photobooth = Photobooth()
    photobooth.getNextFilename = picture_list.getNext

    return photobooth.run(send, recv)


def main(argv):

    config = Config('photobooth.cfg')

    event_recv, event_send = Pipe(duplex=False)
    gui_recv, gui_send = Pipe(duplex=False)

    photobooth = Process(target=main_photobooth, args=(gui_send, event_recv), daemon=True)
    photobooth.start()

    gui = PyQt5Gui(argv, config)
    return gui.run(event_send, gui_recv)
