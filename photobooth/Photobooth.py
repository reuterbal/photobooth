#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from PIL import Image, ImageOps

from .PictureDimensions import PictureDimensions

from . import gui

from .Worker import PictureSaver


class TeardownException(Exception):

    def __init__(self):

        super().__init__()


class Photobooth:

    def __init__(self, config, camera, conn, queue):

        self._conn = conn
        self._queue = queue

        self._worker_list = [PictureSaver(config)]

        self.initCamera(config, camera())
        self.initGpio(config)

        self.triggerOff()


    def initCamera(self, config, camera):

        self._cap = camera
        self._pic_dims = PictureDimensions(config, self._cap.getPicture().size)

        if ( config.getBool('Photobooth', 'show_preview') 
            and self._cap.hasPreview ):
            logging.info('Countdown with preview activated')
            self._show_counter = self.showCounterPreview
        else:
            logging.info('Countdown without preview activated')
            self._show_counter = self.showCounterNoPreview


    def initGpio(self, config):
        
        if config.getBool('Gpio', 'enable'):
            lamp_pin = config.getInt('Gpio', 'lamp_pin')
            trigger_pin = config.getInt('Gpio', 'trigger_pin')
            exit_pin = config.getInt('Gpio', 'exit_pin')

            logging.info('GPIO enabled (lamp_pin=%d, trigger_pin=%d, exit_pin=%d)',
                lamp_pin, trigger_pin, exit_pin)

            from Gpio import Gpio

            self._gpio = Gpio()

            lamp = self._gpio.setLamp(lamp_pin)
            self._lampOn = lambda : self._gpio.lampOn(lamp)
            self._lampOff = lambda : self._gpio.lampOff(lamp)

            self._gpio.setButton(trigger_pin, self.gpioTrigger)
            self._gpio.setButton(exit_pin, self.gpioExit)
        else:
            self._lampOn = lambda : None
            self._lampOff = lambda : None


    def teardown(self):

        logging.info('Teardown of camera')
        self.triggerOff()
        self.setCameraIdle()


    def recvEvent(self, expected):

        event = self._conn.recv()

        try:
            event_idx = expected.index(str(event))
        except ValueError:
            logging.error('Unknown event received: %s', str(event))
            raise ValueError('Unknown event received', str(event))

        return event_idx


    def recvAck(self):

        events = ['ack', 'cancel', 'teardown']

        if self.recvEvent(events) != 0:
            logging.info('Teardown of camera requested')
            raise TeardownException()


    def recvTriggered(self):

        events = ['triggered', 'teardown']

        if self.recvEvent(events) != 0:
            logging.info('Teardown of camera requested')
            raise TeardownException()


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
                    logging.error('Camera error: %s', str(e))
                    self._conn.send( gui.ErrorState('Camera error', str(e)) )
                    self.recvAck()

        except TeardownException:
            self.teardown()
            return 123
        

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


    def enqueueWorkerTasks(self, picture):

        for task in self._worker_list:
            self._queue.put(task.get(picture))


    def trigger(self):

        logging.info('Photobooth triggered')

        self._conn.send(gui.GreeterState())
        self.triggerOff()
        self.setCameraActive()

        self.recvAck()

        pics = self.capturePictures()
        self._conn.send(gui.AssembleState())

        img = self.assemblePictures(pics)
        self._conn.send(gui.PictureState(img))
        
        self.enqueueWorkerTasks(img)

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
