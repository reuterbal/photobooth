#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QMessageBox

from .. import printer
from ..util import lookup_and_import
from .GuiState import PrintState

class GuiPostprocess:

    def __init__(self, **kwargs):

        assert not kwargs


    def get(self, picture):

        raise NotImplementedError()




class PrintPostprocess(GuiPostprocess):

    def __init__(self, printer_module, page_size, **kwargs):

        super().__init__(**kwargs)

        Printer = lookup_and_import(printer.modules, printer_module, 'printer')
        self._printer = Printer(page_size, True)


    def get(self, picture):

        return PrintState(lambda : self.do(picture))

        # reply = QMessageBox.question(parent, 'Print?', 
        #     'Do you want to print the picture?', 
        #     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        # if reply == QMessageBox.Yes:
        #     self._printer.print(picture)


    def do(self, picture):

        print('Printing')
        self._printer.print(picture)
