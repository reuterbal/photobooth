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

import queue

from .. import GuiState
from ..GuiPostprocess import PrintPostprocess


class Postprocessor:

    def __init__(self, config):

        super().__init__()

        self._task_list = []
        self._queue = queue.Queue()

        if config.getBool('Printer', 'enable'):
            module = config.get('Printer', 'module')
            size = (config.getInt('Printer', 'width'),
                    config.getInt('Printer', 'height'))
            self._task_list.append(PrintPostprocess(module, size))

    def fill(self, picture):

        for task in self._task_list:
            self._queue.put(task.get(picture))

    def work(self, msg_box):

        while True:
            try:
                task = self._queue.get(block=False)
            except queue.Empty:
                return

            if isinstance(task, GuiState.PrintState):
                if msg_box.question('Print picture?',
                                    'Do you want to print the picture?'):
                    task.handler()
                    msg_box.information('Printing...',
                                        'Picture sent to printer.')
            else:
                raise ValueError('Unknown task')
