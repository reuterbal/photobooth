#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
