#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from gpiozero import LED, Button 

class Gpio:

    def __init__(self):

        self._buttons = []
        self._lamps = []


    def setButton(self, bcm_pin, handler):

        self._buttons.append(Button(bcm_pin))
        self._buttons[-1].when_pressed = handler


    def setLamp(self, bcm_pin):

        self._lamps.append(LED(bcm_pin))
        return len(self._lamps) - 1


    def lampOn(self, index):

        self._lamps[index].on()


    def lampOff(self, index):

        self._lamps[index].off()


    def lampToggle(self, index):

        self._lamps[index].toggle()
