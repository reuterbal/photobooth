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
