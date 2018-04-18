#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PIL import ImageQt

from PyQt5.QtCore import Qt, QPoint, QSizeF
from PyQt5.QtGui import QPageSize, QPainter, QPixmap
from PyQt5.QtPrintSupport import QPrinter

from . import Printer

class PrinterPyQt5(Printer):

    def __init__(self, page_size):

        super().__init__()

        self._printer = QPrinter(QPrinter.HighResolution)
        self._printer.setOutputFormat(QPrinter.PdfFormat)
        self._printer.setPageSize(QPageSize(QSizeF(*page_size), QPageSize.Millimeter))


    def print(self, filename, picture):
        
        img = ImageQt.ImageQt(picture)
        img = img.scaled(self._printer.pageRect().size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._printer.setOutputFileName(filename)
        painter = QPainter(self._printer)
        painter.drawImage(QPoint(0, 0), img)
        painter.end()
