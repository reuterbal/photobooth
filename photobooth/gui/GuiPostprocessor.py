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

from .. import printer
from ..util import lookup_and_import


class GuiPostprocessor:

    def __init__(self, config):

        super().__init__()

        self._get_task_list = []
        self._do_task_list = []

        if config.getBool('Printer', 'enable'):
            module = config.get('Printer', 'module')
            paper_size = (config.getInt('Printer', 'width'),
                          config.getInt('Printer', 'height'))
            pdf = config.getBool('Printer', 'pdf')
            if config.getBool('Printer', 'confirmation'):
                self._get_task_list.append(
                    PrintPostprocess(module, paper_size, pdf))
            else:
                self._do_task_list.append(
                    PrintPostprocess(module, paper_size, pdf))

    def get(self, picture):

        return [task.get(picture) for task in self._get_task_list]

    def do(self, picture):

        for task in self._do_task_list:
            task.get(picture).action()


class PostprocessTask:

    def __init__(self):

        super().__init__()

    def get(self, picture):

        raise NotImplementedError()


class PostprocessItem:

    def __init__(self, label, action):

        super().__init__()
        self.label = label
        self.action = action

    @property
    def label(self):

        return self._label

    @label.setter
    def label(self, label):

        if not isinstance(label, str):
            raise TypeError('Label must be a string')

        self._label = label

    @property
    def action(self):

        return self._action

    @action.setter
    def action(self, action):

        if not callable(action):
            raise TypeError('Action must be callable')

        self._action = action


class PrintPostprocess(PostprocessTask):

    def __init__(self, printer_module, paper_size, is_pdf, **kwargs):

        super().__init__(**kwargs)

        Printer = lookup_and_import(printer.modules, printer_module, 'printer')
        self._printer = Printer(paper_size, is_pdf)

    def get(self, picture):

        return PostprocessItem('Print', lambda: self._printer.print(picture))
