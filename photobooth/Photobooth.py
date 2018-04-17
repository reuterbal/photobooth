#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from multiprocessing import Pipe, Process

from time import time, sleep, localtime, strftime

import importlib

from PIL import Image, ImageOps

from Config import Config
from PictureList import PictureList
from PictureDimensions import PictureDimensions

import camera, gui


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


def lookup_and_import(module_list, name, package=None):

    result = next(((mod_name, class_name) 
                for config_name, mod_name, class_name in module_list
                if name == config_name), None)
    print(result)
    
    if package == None:
        import_module = importlib.import_module(result[0])
    else:
        import_module = importlib.import_module('.' + result[0], package)

    if result[1] == None:
        return import_module
    else:
        return getattr(import_module, result[1])


def main_photobooth(config, send, recv):

    while True:
        try:
            Camera = lookup_and_import(camera.modules, config.get('Camera', 'module'), 'camera')

            with Camera() as cap:
                photobooth = Photobooth(config, cap)
                return photobooth.run(send, recv)

        except BaseException as e:
            send.send( gui.ErrorState('Camera error', str(e)) )
            event = recv.recv()
            if str(event) != 'ack':
                    print('Unknown event received: ' + str(event))
                    raise RuntimeError('Unknown event received', str(event))


def run(argv):

    config = Config('photobooth.cfg')

    event_recv, event_send = Pipe(duplex=False)
    gui_recv, gui_send = Pipe(duplex=False)

    photobooth = Process(target=main_photobooth, args=(config, gui_send, event_recv), daemon=True)
    photobooth.start()

    Gui = lookup_and_import(gui.modules, config.get('Gui', 'module'), 'gui')
    return Gui(argv, config).run(event_send, gui_recv)


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
