#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .. import printer
from ..util import lookup_and_import

from PyQt5.QtWidgets import QMessageBox

class GuiPostprocess:

    def __init__(self, **kwargs):

        assert not kwargs


    def do(self, parent, picture):

        raise NotImplementedError()




class PrintPostprocess(GuiPostprocess):

    def __init__(self, printer_module, page_size, **kwargs):

        super().__init__(**kwargs)

        Printer = lookup_and_import(printer.modules, printer_module, 'printer')
        self._printer = Printer(page_size, True)


    def do(self, parent, picture):

        reply = QMessageBox.question(parent, 'Print?', 
            'Do you want to print the picture?', 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self._printer.print(picture)
