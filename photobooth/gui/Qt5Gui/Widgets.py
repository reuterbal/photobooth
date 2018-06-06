#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import ceil

from PyQt5 import Qt
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets


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

        text = '{}'.format(ceil(self.value))

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
