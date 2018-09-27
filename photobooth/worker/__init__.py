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

from time import localtime, strftime

from .PictureList import PictureList
from .. import StateMachine
from ..Threading import Workers


class WorkerTask:

    def __init__(self, **kwargs):

        assert not kwargs

    def do(self, picture):

        raise NotImplementedError()


class PictureSaver(WorkerTask):

    def __init__(self, basename):

        super().__init__()

        self._pic_list = PictureList(basename)

    def do(self, picture):

        filename = self._pic_list.getNext()
        logging.info('Saving picture as %s', filename)
        with open(filename, 'wb') as f:
            f.write(picture.getbuffer())


class Worker:

    def __init__(self, config, comm):

        self._comm = comm

        self.initPostprocessTasks(config)
        self.initPictureTasks(config)

    def initPostprocessTasks(self, config):

        self._postprocess_tasks = []

        # PictureSaver for assembled pictures
        path = os.path.join(config.get('Storage', 'basedir'),
                            config.get('Storage', 'basename'))
        basename = strftime(path, localtime())
        self._postprocess_tasks.append(PictureSaver(basename))

    def initPictureTasks(self, config):

        self._picture_tasks = []

        # PictureSaver for single shots
        path = os.path.join(config.get('Storage', 'basedir'),
                            config.get('Storage', 'basename') + '_shot_')
        basename = strftime(path, localtime())
        self._picture_tasks.append(PictureSaver(basename))

    def run(self):

        for state in self._comm.iter(Workers.WORKER):
            self.handleState(state)

        return True

    def handleState(self, state):

        if isinstance(state, StateMachine.TeardownState):
            self.teardown(state)
        elif isinstance(state, StateMachine.ReviewState):
            self.doPostprocessTasks(state.picture)
        elif isinstance(state, StateMachine.CameraEvent):
            if state.name == 'capture':
                self.doPictureTasks(state.picture)
            else:
                raise ValueError('Unknown CameraEvent "{}"'.format(state))

    def teardown(self, state):

        pass

    def doPostprocessTasks(self, picture):

        for task in self._postprocess_tasks:
            task.do(picture)

    def doPictureTasks(self, picture):

        for task in self._picture_tasks:
            task.do(picture)
