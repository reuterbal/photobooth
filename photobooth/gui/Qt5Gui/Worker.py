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

from PyQt5 import QtCore


class Worker(QtCore.QThread):

    def __init__(self, comm):

        super().__init__()
        self._comm = comm
        self._queue = queue.Queue()

    def put(self, task):

        self._queue.put(task)

    def get(self):

        return self._queue.get()

    def done(self):

        self._queue.task_done()

    def run(self):

        while True:
            task = self.get()
            if task is None:
                break
            task()
            self.done()
