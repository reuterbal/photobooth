#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from PyQt5.QtWidgets import QMessageBox

from .. import printer
from ..util import lookup_and_import
from .GuiState import PrintState

class GuiPostprocess:

    def __init__(self, **kwargs):

        assert not kwargs


    def get(self, picture):

        raise NotImplementedError()


    def confirm(self, picture):

        raise NotImplementedError()




class PrintPostprocess(GuiPostprocess):

    def __init__(self, printer_module, page_size, **kwargs):

        super().__init__(**kwargs)

        Printer = lookup_and_import(printer.modules, printer_module, 'printer')
        self._printer = Printer(page_size)


    def get(self, picture):

        return PrintState(lambda : self.do(picture), False)


    def confirm(self, picture):

        return PrintState(lambda : None, True)


    def do(self, picture):

        logging.info('Printing picture')
        self._printer.print(picture)
