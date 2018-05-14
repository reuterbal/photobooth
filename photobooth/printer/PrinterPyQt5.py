#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from PIL import ImageQt

from PyQt5.QtCore import Qt, QPoint, QSizeF
from PyQt5.QtGui import QPageSize, QPainter, QPixmap
from PyQt5.QtPrintSupport import QPrinter

from . import Printer

class PrinterPyQt5(Printer):

    def __init__(self, page_size, print_pdf=False):

        super().__init__(page_size)

        self._printer = QPrinter(QPrinter.HighResolution)
        self._printer.setPageSize(QPageSize(QSizeF(*page_size), QPageSize.Millimeter))

        logging.info('Using printer "%s"', self._printer.printerName())

        self._print_pdf = print_pdf
        if self._print_pdf:
            logging.info('Using PDF printer')
            self._counter = 0
            self._printer.setOutputFormat(QPrinter.PdfFormat)
            self._printer.setFullPage(True)


    def print(self, picture):
        
        if self._print_pdf:
            self._printer.setOutputFileName('print_' + str(self._counter) + '.pdf')
            self._counter += 1

        img = ImageQt.ImageQt(picture)
        img = img.scaled(self._printer.pageRect().size(), Qt.KeepAspectRatio, 
            Qt.SmoothTransformation)

        printable_size = self._printer.pageRect(QPrinter.DevicePixel)
        origin = ( (printable_size.width() - img.width()) // 2,
                   (printable_size.height() - img.height()) // 2 )
        
        painter = QPainter(self._printer)
        painter.drawImage(QPoint(*origin), img)
        painter.end()
