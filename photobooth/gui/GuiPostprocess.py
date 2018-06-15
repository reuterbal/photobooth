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
        self._printer = Printer(page_size, True)

    def get(self, picture):

        return PrintState(lambda: self.do(picture), False)

    def confirm(self, picture):

        return PrintState(lambda: None, True)

    def do(self, picture):

        logging.info('Printing picture')
        self._printer.print(picture)
