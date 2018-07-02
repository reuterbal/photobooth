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

import math

from PyQt5 import Qt
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets


class SpinningWaitClock(QtWidgets.QWidget):
    # Spinning wait clock, inspired by
    # https://wiki.python.org/moin/PyQt/A%20full%20widget%20waiting%20indicator

    def __init__(self):

        super().__init__()

        self._num_dots = 8
        self._value = 0

    @property
    def value(self):

        return self._value

    @value.setter
    def value(self, value):

        if self._value != value:
            self._value = value
            self.update()

    def showEvent(self, event):

        self.startTimer(100)

    def timerEvent(self, event):

        self.value += 1

    def paintEvent(self, event):

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))

        dots = self._num_dots
        center = (self.width() / 2, self.height() / 2)
        pos = self.value % dots

        for dot in range(dots):
            distance = (pos - dot) % dots
            offset = (180 / dots * math.cos(2 * math.pi * dot / dots) - 20,
                      180 / dots * math.sin(2 * math.pi * dot / dots) - 20)

            color = (distance + 1) / (dots + 1) * 255
            painter.setBrush(QtGui.QBrush(QtGui.QColor(color, color, color)))

            painter.drawEllipse(center[0] + offset[0], center[1] + offset[1],
                                15, 15)

        painter.end()


class RoundProgressBar(QtWidgets.QWidget):
    # Adaptation of QRoundProgressBar from
    # https://sourceforge.net/projects/qroundprogressbar/
    # to PyQt5, using the PyQt4-version offered at
    # https://stackoverflow.com/a/33583019

    def __init__(self, begin, end, value):

        super().__init__()

        self._begin = begin
        self._end = end
        self._value = value

        self._data_pen_width = 7
        self._outline_pen_width = 10
        self._null_position = 90

    @property
    def value(self):

        return self._value

    @value.setter
    def value(self, value):

        if self._value != value:
            if value < self._begin:
                self._value = self._begin
            elif value > self._end:
                self._value = self._end
            else:
                self._value = value

    def _drawBase(self, painter, base_rect):

        color = self.palette().base().color()
        color.setAlpha(100)
        brush = self.palette().base()
        brush.setColor(color)
        painter.setPen(QtGui.QPen(self.palette().base().color(),
                                  self._outline_pen_width))
        painter.setBrush(brush)

        painter.drawEllipse(base_rect.adjusted(self._outline_pen_width // 2,
                                               self._outline_pen_width // 2,
                                               -self._outline_pen_width // 2,
                                               -self._outline_pen_width // 2))

    def _drawCircle(self, painter, base_rect):

        if self.value == self._begin:
            return

        arc_length = 360 / (self._end - self._begin) * self.value

        painter.setPen(QtGui.QPen(self.palette().text().color(),
                                  self._data_pen_width))
        painter.setBrush(Qt.Qt.NoBrush)
        painter.drawArc(base_rect.adjusted(self._outline_pen_width // 2,
                                           self._outline_pen_width // 2,
                                           -self._outline_pen_width // 2,
                                           -self._outline_pen_width // 2),
                        self._null_position * 16, -arc_length * 16)

    def _drawText(self, painter, inner_rect, inner_radius):

        text = '{}'.format(math.ceil(self.value))

        f = self.font()
        f.setPixelSize(inner_radius * 0.8 / len(text))
        painter.setFont(f)
        painter.setPen(self.palette().text().color())

        painter.drawText(inner_rect, Qt.Qt.AlignCenter, text)

    def paintEvent(self, event):

        outer_radius = min(self.width(), self.height())
        inner_radius = outer_radius - self._outline_pen_width
        delta = (outer_radius - inner_radius) / 2

        base_rect = QtCore.QRectF(1, 1, outer_radius - 2, outer_radius - 2)
        inner_rect = QtCore.QRectF(delta, delta, inner_radius, inner_radius)

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # base circle
        self._drawBase(painter, base_rect)

        # data circle
        self._drawCircle(painter, base_rect)

        # text
        self._drawText(painter, inner_rect, inner_radius)

        painter.end()


class TransparentOverlay(QtWidgets.QWidget):

    def __init__(self, parent, timeout=None, timeout_handle=None):

        super().__init__(parent)
        self.setObjectName('TransparentOverlay')

        rect = parent.rect()
        rect.adjust(50, 50, -50, -50)
        self.setGeometry(rect)

        if timeout is not None:
            self._handle = timeout_handle
            self._timer = self.startTimer(timeout)

        self.show()

    def paintEvent(self, event):

        opt = QtWidgets.QStyleOption()
        opt.initFrom(self)
        painter = QtGui.QPainter(self)
        self.style().drawPrimitive(QtWidgets.QStyle.PE_Widget, opt, painter,
                                   self)
        painter.end()

    def timerEvent(self, event):

        self.killTimer(self._timer)
        self._handle()
