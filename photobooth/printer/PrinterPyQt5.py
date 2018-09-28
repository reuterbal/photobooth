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

from PyQt5 import QtCore, QtGui
from PyQt5.QtPrintSupport import QPrinter

from . import Printer


class PrinterPyQt5(Printer):

    def __init__(self, page_size, print_pdf=False):

        super().__init__(page_size)

        self._printer = QPrinter(QPrinter.HighResolution)
        self._printer.setPageSize(QtGui.QPageSize(QtCore.QSizeF(*page_size),
                                                  QtGui.QPageSize.Millimeter))
        self._printer.setColorMode(QPrinter.Color)

        logging.info('Using printer "%s"', self._printer.printerName())

        self._print_pdf = print_pdf
        if self._print_pdf:
            logging.info('Using PDF printer')
            self._counter = 0
            self._printer.setOutputFormat(QPrinter.PdfFormat)
            self._printer.setFullPage(True)

    def print(self, picture):

        if self._print_pdf:
            self._printer.setOutputFileName('print_%d.pdf' % self._counter)
            self._counter += 1

        logging.info('Printing picture')

        picture = picture.scaled(self._printer.paperRect().size(),
                                 QtCore.Qt.KeepAspectRatio,
                                 QtCore.Qt.SmoothTransformation)

        printable_size = self._printer.pageRect(QPrinter.DevicePixel)
        origin = ((printable_size.width() - picture.width()) // 2,
                  (printable_size.height() - picture.height()) // 2)

        painter = QtGui.QPainter(self._printer)
        painter.drawImage(QtCore.QPoint(*origin), picture)
        painter.end()
