#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from time import time, sleep, localtime, strftime

from PIL import Image, ImageOps

from .PictureList import PictureList
from .PictureDimensions import PictureDimensions

from . import gui

class Photobooth:

    def __init__(self, config, camera):

        self.initCamera(config, camera)
        self.initGpio(config)
        self.initTimings(config)

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
            self._gpio.setButton(config.getInt('Gpio', 'exit_pin'), self.teardown)
        else:
            self._lampOn = lambda : None
            self._lampOff = lambda : None


    def initTimings(self, config):

        self._greeter_time = config.getInt('Photobooth', 'greeter_time')
        self._countdown_time = config.getInt('Photobooth', 'countdown_time')
        self._display_time = config.getInt('Photobooth', 'display_time')


    def teardown(self):

        self.triggerOff()
        self.setCameraIdle()


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


    def initRun(self):

        self.setCameraIdle()
        self._send.send(gui.IdleState())
        self.triggerOn()


    def run(self, send, recv):

        self._send = send
        self._recv = recv
        self.initRun()

        while True:
            try:
                event = self._recv.recv()

                if str(event) == 'start':
                    print('Camera already started')
                    self.initRun()
                    continue
                elif str(event) != 'triggered':
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
                    event = self._recv.recv()
                    if str(event) == 'cancel':
                        self.teardown()
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

        self._send.send(gui.CountdownState())

        while not self._recv.poll():
            toc = time() - tic
            self._send.send( gui.PreviewState(
                message = str(self.countdownTime - int(toc)), 
                picture = ImageOps.mirror(self._cap.getPreview()) ) )

        event = self._recv.recv()
        if str(event) == 'cancel':
            self.teardown()
            return 1
        elif str(event) == 'ack':
            pass
        else:
            print('Unknown event received: ' + str(event))
            raise RuntimeError('Unknown event received', str(event))


    def showCounterNoPreview(self):

        self._send.send(gui.CountdownState())

        for i in range(self.countdownTime):
            self._send.send( gui.PreviewState(
                message = str(self.countdownTime - i),
                picture = Image.new('RGB', (1,1), 'white') ) )
            sleep(1)

        event = self._recv.recv()
        if str(event) == 'cancel':
            self.teardown()
            return 1
        elif str(event) == 'ack':
            pass
        else:
            print('Unknown event received: ' + str(event))
            raise RuntimeError('Unknown event received', str(event))


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

        return [ self.captureSinglePicture() for _ in range(self._pic_dims.totalNumPictures) ]


    def trigger(self):

        self._send.send(gui.GreeterState())
        self.triggerOff()
        self.setCameraActive()

        event = self._recv.recv()
        if str(event) == 'cancel':
            self.teardown()
            return 1
        elif str(event) == 'ack':
            pass
        else:
            print('Unknown event received: ' + str(event))
            raise RuntimeError('Unknown event received', str(event))

        pics = self.capturePictures()
        self._send.send(gui.AssembleState())

        img = self.assemblePictures(pics)
        img.save(self.getNextFilename(), 'JPEG')
        self._send.send(gui.PictureState(img))

        self.setCameraIdle()

        event = self._recv.recv()
        if str(event) == 'cancel':
            self.teardown()
            return 1
        elif str(event) == 'ack':
            pass
        else:
            print('Unknown event received: ' + str(event))
            raise RuntimeError('Unknown event received', str(event))

        self._send.send(gui.IdleState())
        self.triggerOn()


    def gpioTrigger(self):

        self._gpioTrigger()


    def triggerOff(self):

        self._lampOff()
        self._gpioTrigger = lambda : None


    def triggerOn(self):

        self._lampOn()
        self._gpioTrigger = lambda : self._send.send(Gui.TriggerState())
