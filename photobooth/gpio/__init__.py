#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Photobooth - a flexible photo booth software
# Copyright (C) 2018  Balthasar Reuter <photobooth at re - web dot eu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import logging
from colorsys import hsv_to_rgb
from time import sleep

from .. import StateMachine
from ..Threading import Workers


class Gpio:

    def __init__(self, config, comm):

        super().__init__()

        self._comm = comm
        self._gpio = None

        self._is_trigger = False
        self._is_enabled = config.getBool('Gpio', 'enable')
        self._countdown_time = config.getInt('Photobooth', 'countdown_time')

        self.initGpio(config)

    def initGpio(self, config):

        if self._is_enabled:
            self._gpio = Entities()

            lamp_pin = config.getInt('Gpio', 'lamp_pin')
            trigger_pin = config.getInt('Gpio', 'trigger_pin')
            exit_pin = config.getInt('Gpio', 'exit_pin')

            rgb_pin = (config.getInt('Gpio', 'chan_r_pin'),
                       config.getInt('Gpio', 'chan_g_pin'),
                       config.getInt('Gpio', 'chan_b_pin'))

            logging.info(('GPIO enabled (lamp_pin=%d, trigger_pin=%d, '
                         'exit_pin=%d, rgb_pins=(%d, %d, %d))'),
                         lamp_pin, trigger_pin, exit_pin, *rgb_pin)

            self._gpio.setButton(trigger_pin, self.trigger)
            self._gpio.setButton(exit_pin, self.exit)
            self._lamp = self._gpio.setLamp(lamp_pin)
            self._rgb = self._gpio.setRgb(rgb_pin)
        else:
            logging.info('GPIO disabled')

    def run(self):

        for state in self._comm.iter(Workers.GPIO):
            self.handleState(state)

        return True

    def handleState(self, state):

        if isinstance(state, StateMachine.IdleState):
            self.showIdle()
        elif isinstance(state, StateMachine.GreeterState):
            self.showGreeter()
        elif isinstance(state, StateMachine.CountdownState):
            self.showCountdown()
        elif isinstance(state, StateMachine.CaptureState):
            self.showCapture()
        elif isinstance(state, StateMachine.AssembleState):
            self.showAssemble()
        elif isinstance(state, StateMachine.ReviewState):
            self.showReview()
        elif isinstance(state, StateMachine.PostprocessState):
            self.showPostprocess()
        elif isinstance(state, StateMachine.TeardownState):
            self.teardown(state)

    def teardown(self, state):

        if self._is_enabled:
            self._gpio.teardown()

    def enableTrigger(self):

        if self._is_enabled:
            self._is_trigger = True
            self._gpio.lampOn(self._lamp)

    def disableTrigger(self):

        if self._is_enabled:
            self._is_trigger = False
            self._gpio.lampOff(self._lamp)

    def setRgbColor(self, r, g, b):

        if self._is_enabled:
            self._gpio.rgbColor(self._rgb, (r, g, b))

    def rgbOn(self):

        if self._is_enabled:
            self._gpio.rgbOn(self._rgb)

    def rgbOff(self):

        if self._is_enabled:
            self._gpio.rgbOff(self._rgb)

    def rgbBlink(self):

        if self._is_enabled:
            self._gpio.rgbBlink(self._rgb, 0.5, 0.5, 0.1, 0.1, (1, 0, 0),
                                (0, 0, 0), self._countdown_time)

    def trigger(self):

        if self._is_trigger:
            self.disableTrigger()
            self._comm.send(Workers.MASTER, StateMachine.GpioEvent('trigger'))

    def exit(self):

        self._comm.send(
            Workers.MASTER,
            StateMachine.TeardownEvent(StateMachine.TeardownEvent.WELCOME))

    def showIdle(self):

        self.enableTrigger()

        if self._is_enabled:
            h, s, v = 0, 1, 1
            while self._comm.empty(Workers.GPIO):
                h = (h + 1) % 360
                rgb = hsv_to_rgb(h / 360, s, v)
                self.setRgbColor(*rgb)
                sleep(0.1)

    def showGreeter(self):

        self.disableTrigger()
        self.rgbOff()

    def showCountdown(self):

        sleep(0.2)
        self.rgbBlink()

    def showCapture(self):

        self.rgbOn()
        self.setRgbColor(1, 1, .9)

    def showAssemble(self):

        self.rgbOff()

    def showReview(self):

        self.setRgbColor(0, .15, 0)

    def showPostprocess(self):

        pass


class Entities:

    def __init__(self):

        super().__init__()

        import gpiozero
        self.LED = gpiozero.LED
        self.RGBLED = gpiozero.RGBLED
        self.Button = gpiozero.Button
        self.GPIOPinInUse = gpiozero.GPIOPinInUse

        self._buttons = []
        self._lamps = []
        self._rgb = []

    def teardown(self):

        for l in self._lamps:
            l.off()

        for l in self._rgb:
            l.off()

    def setButton(self, bcm_pin, handler):

        try:
            self._buttons.append(self.Button(bcm_pin))
            self._buttons[-1].when_pressed = handler
        except self.GPIOPinInUse:
            logging.error('Pin {} already in use!'.format(bcm_pin))

    def setLamp(self, bcm_pin):

        try:
            self._lamps.append(self.LED(bcm_pin))
            return len(self._lamps) - 1
        except self.GPIOPinInUse:
            logging.error('Pin {} already in use!'.format(bcm_pin))
            return None

    def setRgb(self, bcm_pins):

        try:
            led = self.RGBLED(*bcm_pins)
            for l in led._leds:
                l.frequency = 140
            self._rgb.append(led)
            return len(self._rgb) - 1
        except self.GPIOPinInUse:
            logging.error('Some pin {} already in use!'.format(bcm_pins))
            return None

    def lampOn(self, index):

        if index is not None:
            self._lamps[index].on()

    def lampOff(self, index):

        if index is not None:
            self._lamps[index].off()

    def lampToggle(self, index):

        if index is not None:
            self._lamps[index].toggle()

    def rgbOn(self, index):

        if index is not None:
            self._rgb[index].on()

    def rgbOff(self, index):

        if index is not None:
            self._rgb[index].off()

    def rgbColor(self, index, color):

        if index is not None:
            self._rgb[index].color = color

    def rgbBlink(self, index, on_time, off_time, fade_in_time, fade_out_time,
                 on_color, off_color, count):

        if index is not None:
            self._rgb[index].blink(on_time, off_time, fade_in_time,
                                   fade_out_time, on_color, off_color, count)
