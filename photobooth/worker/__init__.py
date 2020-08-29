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

import os.path

from time import localtime, strftime

from .. import StateMachine
from ..Threading import Workers

from .PictureList import PictureList
from .PictureMailer import PictureMailer
from .PictureSaver import PictureSaver
from .PictureUploadWebdav import PictureUploadWebdav
from .PictureList import PictureList


class Worker:

    def __init__(self, config, comm):

        self._comm = comm

        # Picture naming convention for assembled pictures
        path = os.path.join(config.get('Storage', 'basedir'),
                            config.get('Storage', 'basename'))
        basename = strftime(path, localtime())
        self._pic_list = PictureList(basename)

        self.initPostprocessTasks(config)
        self.initPictureTasks(config)

    def initPostprocessTasks(self, config):

        self._postprocess_tasks = []

        # PictureSaver for assembled pictures
        self._postprocess_tasks.append(PictureSaver())

        # PictureMailer for assembled pictures
        if config.getBool('Mailer', 'enable'):
            self._postprocess_tasks.append(PictureMailer(config))

        # PictureUploadWebdav to upload pictures to a webdav storage
        if config.getBool('UploadWebdav', 'enable'):
            self._postprocess_tasks.append(PictureUploadWebdav(config))

    def initPictureTasks(self, config):

        self._picture_tasks = []

        # PictureSaver for single shots
        self._picture_tasks.append(PictureSaver())

    def run(self):

        for state in self._comm.iter(Workers.WORKER):
            self.handleState(state)

        return True

    def handleState(self, state):

        if isinstance(state, StateMachine.TeardownState):
            self.teardown(state)
        elif isinstance(state, StateMachine.ReviewState):
            picturename = self._pic_list.getNextPic()
            self.doPostprocessTasks(state.picture, picturename)
        elif isinstance(state, StateMachine.CameraEvent):
            if state.name == 'capture':
                picturename = self._pic_list.getNextPicShot()
                self.doPictureTasks(state.picture, picturename)
            else:
                raise ValueError('Unknown CameraEvent "{}"'.format(state))

    def teardown(self, state):

        pass

    def doPostprocessTasks(self, picture, picturename):

        for task in self._postprocess_tasks:
            task.do(picture, picturename)

    def doPictureTasks(self, picture, picturename):

        for task in self._picture_tasks:
            task.do(picture, picturename)
