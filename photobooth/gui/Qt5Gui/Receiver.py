#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import multiprocessing as mp

from PyQt5 import QtCore


class Receiver(QtCore.QThread):

    notify = QtCore.pyqtSignal(object)

    def __init__(self, conn):

        super().__init__()
        self._conn = conn

    def handle(self, state):

        self.notify.emit(state)

    def run(self):

        while self._conn:
            for c in mp.connection.wait(self._conn):
                try:
                    state = c.recv()
                except EOFError:
                    break
                else:
                    self.handle(state)
