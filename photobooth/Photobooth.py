#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from time import time, sleep, localtime, strftime

from PIL import Image, ImageOps

from .PictureList import PictureList
from .PictureDimensions import PictureDimensions

from . import gui


class TeardownException(Exception):

    def __init__(self):

        super().__init__()


class Photobooth:

    def __init__(self, config, camera, conn):

        self._conn = conn

        self.initCamera(config, camera)
        self.initGpio(config)

        self.triggerOff()


    def initCamera(self, config, camera):

        self._cap = camera
        self._pic_dims = PictureDimensions(config, self._cap.getPicture().size)

        picture_basename = strftime(config.get('Picture', 'basename'), localtime())        
        self._pic_list = PictureList(picture_basename)
        self._get_next_filename = self._pic_list.getNext

        if ( config.getBool('Photobooth', 'show_preview') 
            and self._cap.hasPreview ):
            self._show_counter = self.showCounterPreview
        else:
            self._show_counter = self.showCounterNoPreview


    def initGpio(self, config):
        
        if config.getBool('Gpio', 'enable'):
            from Gpio import Gpio

            self._gpio = Gpio()

            lamp = self._gpio.setLamp(config.getInt('Gpio', 'lamp_pin'))
            self._lampOn = lambda : self._gpio.lampOn(lamp)
            self._lampOff = lambda : self._gpio.lampOff(lamp)

            self._gpio.setButton(config.getInt('Gpio', 'trigger_pin'), self.gpioTrigger)
            self._gpio.setButton(config.getInt('Gpio', 'exit_pin'), self.gpioExit)
        else:
            self._lampOn = lambda : None
            self._lampOff = lambda : None


    def teardown(self):

        print('Camera teardown')
        self.triggerOff()
        self.setCameraIdle()


    def recvEvent(self, expected):

        event = self._conn.recv()

        try:
            event_idx = expected.index(str(event))
        except ValueError:
            print('Photobooth: Unknown event received: ' + str(event))
            raise ValueError('Unknown event received', str(event))

        return event_idx


    def recvAck(self):

        events = ['ack', 'cancel', 'teardown']

        if self.recvEvent(events) != 0:
            print('Teardown of Photobooth requested')
            raise TeardownException()


    def recvTriggered(self):

        events = ['triggered', 'teardown']

        if self.recvEvent(events) != 0:
            print('Teardown of Photobooth requested')
            raise TeardownException()


    @property
    def getNextFilename(self):

        return self._get_next_filename


    @property
    def showCounter(self):

        return self._show_counter


    def initRun(self):

        self.setCameraIdle()
        self._conn.send(gui.IdleState())
        self.triggerOn()


    def run(self):

        self.initRun()

        try:
            while True:
                try:
                    self.recvTriggered()
                except EOFError:
                    return 0

                try:
                    self.trigger()
                except RuntimeError as e:
                    print('Camera error: ' + str(e))
                    self._conn.send( gui.ErrorState('Camera error', str(e)) )
                    self.recvAck()

        except TeardownException:
            return -1
        

    def setCameraActive(self):

        self._cap.setActive()
        

    def setCameraIdle(self):

        if self._cap.hasIdle:
            self._cap.setIdle()


    def showCounterPreview(self):

        self._conn.send(gui.CountdownState())

        while not self._conn.poll():
            self._conn.send( 
                gui.PreviewState(picture = ImageOps.mirror(self._cap.getPreview())) )

        self.recvAck()


    def showCounterNoPreview(self):

        self._conn.send(gui.CountdownState())
        self.recvAck()
        print('ack received')


    def showPose(self):

        self._conn.send(gui.PoseState())


    def captureSinglePicture(self):

        self.showCounter()
        self.showPose()
        return self._cap.getPicture()


    def capturePictures(self):

        return [ self.captureSinglePicture() for _ in range(self._pic_dims.totalNumPictures) ]


    def assemblePictures(self, pictures):

        output_image = Image.new('RGB', self._pic_dims.outputSize, (255, 255, 255))

        for i in range(self._pic_dims.totalNumPictures):
            output_image.paste(pictures[i].resize(self._pic_dims.thumbnailSize), 
                self._pic_dims.thumbnailOffset[i])

        return output_image


    def trigger(self):

        self._conn.send(gui.GreeterState())
        self.triggerOff()
        self.setCameraActive()

        self.recvAck()

        pics = self.capturePictures()
        self._conn.send(gui.AssembleState())

        img = self.assemblePictures(pics)
        img.save(self.getNextFilename(), 'JPEG')
        self._conn.send(gui.PictureState(img))

        self.setCameraIdle()

        self.recvAck()

        self._conn.send(gui.IdleState())
        self.triggerOn()


    def gpioTrigger(self):

        self._gpioTrigger()


    def gpioExit(self):

        self._conn.send(gui.TeardownState())


    def triggerOff(self):

        self._lampOff()
        self._gpioTrigger = lambda : None


    def triggerOn(self):

        self._lampOn()
        self._gpioTrigger = lambda : self._conn.send(gui.TriggerState())
