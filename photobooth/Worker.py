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
import os.path
import sys

from time import localtime, strftime

from .PictureList import PictureList
from .StateMachine import TeardownEvent, TeardownState
from .Threading import Workers


class WorkerTask:

    def __init__(self, **kwargs):

        assert not kwargs

    def get(self, picture):

        raise NotImplementedError()


class PictureSaver(WorkerTask):

    def __init__(self, config):

        super().__init__()

        path = os.path.join(config.get('Picture', 'basedir'),
                            config.get('Picture', 'basename'))
        basename = strftime(path, localtime())
        self._pic_list = PictureList(basename)

    @staticmethod
    def do(picture, filename):

        logging.info('Saving picture as %s', filename)
        picture.save(filename, 'JPEG')

    def get(self, picture):

        return (self.do, (picture, self._pic_list.getNext()))


class Worker:

    def __init__(self, config, comm):

        self._comm = comm

    def run(self):

        for state in self._comm.iter(Workers.WORKER):
            self.handleState(state)

    def handleState(self, state):

        if isinstance(state, TeardownState):
            self.teardown(state)

    def teardown(self, state):

        if state.target == TeardownEvent.EXIT:
            sys.exit(0)
        elif state.target == TeardownEvent.RESTART:
            sys.exit(123)
