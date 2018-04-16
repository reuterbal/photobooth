#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from Config import Config

from PictureList import PictureList
from PictureDimensions import PictureDimensions

import Gui
from PyQt5Gui import PyQt5Gui

from PIL import Image, ImageOps

from multiprocessing import Pipe, Process

from time import time, sleep, localtime, strftime



class Photobooth:

    def __init__(self, config, camera):

        picture_basename = strftime(config.get('Picture', 'basename'), localtime())

        self._cap = camera
        self._pic_dims = PictureDimensions(config, self._cap.getPicture().size)
        self._pic_list = PictureList(picture_basename)

        self._pose_time = config.getInt('Photobooth', 'pose_time')
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
    def poseTime(self):

        return self._pose_time


    @property
    def countdownTime(self):

        return self._countdown_time


    @property
    def displayTime(self):

        return self._display_time


    def run(self, send, recv):

        self._send = send
        self.setCameraIdle()

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

        while toc < self.countdownTime:
            self._send.send( Gui.PreviewState(
                message = str(self.countdownTime - int(toc)), 
                picture = ImageOps.mirror(self._cap.getPreview()) ) )
            toc = time() - tic


    def showCounterNoPreview(self):

        for i in range(self.countdownTime):
            self._send.send( Gui.PreviewState(
                message = str(i),
                picture = Image.new('RGB', (1,1), 'white') ) )
            sleep(1)


    def captureSinglePicture(self):

        self.showCounter()

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

        self._send.send(Gui.PoseState())
        self.setCameraActive()

        sleep(self.poseTime)

        img = self.capturePictures()
        img.save(self.getNextFilename(), 'JPEG')
        self._send.send(Gui.PictureState(img))

        self.setCameraIdle()

        sleep(self.displayTime)

        self._send.send(Gui.IdleState())


def main_photobooth(config, send, recv):

    if config.get('Camera', 'module') == 'python-gphoto2':
        from CameraGphoto2 import CameraGphoto2 as Camera
    elif config.get('Camera', 'module') == 'gphoto2-cffi':
        from CameraGphoto2Cffi import CameraGphoto2Cffi as Camera
    elif config.get('Camera', 'module') == 'gphoto2-commandline':
        from CameraGphoto2CommandLine import CameraGphoto2CommandLine as Camera
    elif config.get('Camera', 'module') == 'opencv':
        from CameraOpenCV import CameraOpenCV as Camera
    else:
        raise ImportError('Unknown camera module "' + config.get('Camera', 'module') + '"')

    with Camera() as cap:
        photobooth = Photobooth(config, cap)
        return photobooth.run(send, recv)


def run(argv):

    config = Config('photobooth.cfg')

    event_recv, event_send = Pipe(duplex=False)
    gui_recv, gui_send = Pipe(duplex=False)

    photobooth = Process(target=main_photobooth, args=(config, gui_send, event_recv), daemon=True)
    photobooth.start()

    gui = PyQt5Gui(argv, config)
    return gui.run(event_send, gui_recv)


def main(argv):

    known_status_codes = {
        -1: 'Initializing photobooth',
        -2: 'Restarting photobooth and reloading config'
    }

    status_code = -1

    while status_code in known_status_codes:
        print(known_status_codes[status_code])

        status_code = run(argv)

    return status_code
