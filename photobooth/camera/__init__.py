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

from PIL import Image, ImageOps
from io import BytesIO

from .PictureDimensions import PictureDimensions
from .. import StateMachine
from ..Threading import Workers

# Available camera modules as tuples of (config name, module name, class name)
modules = (
    ('python-gphoto2', 'CameraGphoto2', 'CameraGphoto2'),
    ('gphoto2-cffi', 'CameraGphoto2Cffi', 'CameraGphoto2Cffi'),
    ('gphoto2-commandline', 'CameraGphoto2CommandLine',
     'CameraGphoto2CommandLine'),
    ('opencv', 'CameraOpenCV', 'CameraOpenCV'),
    ('picamera', 'CameraPicamera', 'CameraPicamera'),
    ('dummy', 'CameraDummy', 'CameraDummy'))


class Camera:

    def __init__(self, config, comm, CameraModule):

        super().__init__()

        self._comm = comm
        self._cfg = config
        self._cam = CameraModule

        self._cap = None
        self._pic_dims = None

        self._is_preview = self._cfg.getBool('Photobooth', 'show_preview')
        self._is_keep_pictures = self._cfg.getBool('Storage', 'keep_pictures')

        self._gif_num_frames = self._cfg.getInt('GIF', 'num_frames')
        self._gif_num_img_to_take = ((self._gif_num_frames - 2) // 2) + 2
        self._gif_frame_duration = self._cfg.getInt('GIF', 'frame_duration')
        self._gif_use_nth_capture = self._cfg.getInt('GIF', 'use_nth_capture')

        rot_vals = {0: None, 90: Image.ROTATE_90, 180: Image.ROTATE_180,
                    270: Image.ROTATE_270}
        self._rotation = rot_vals[self._cfg.getInt('Camera', 'rotation')]

    def startup(self):

        self._cap = self._cam()

        logging.info('Using camera {} preview functionality'.format(
            'with' if self._is_preview else 'without'))

        test_picture = self._cap.getPicture()
        if self._rotation is not None:
            test_picture = test_picture.transpose(self._rotation)

        self._pic_dims = PictureDimensions(self._cfg, test_picture.size)
        self._is_preview = self._is_preview and self._cap.hasPreview

        background = self._cfg.get('Picture', 'background')
        if len(background) > 0:
            logging.info('Using background "{}"'.format(background))
            bg_picture = Image.open(background)
            self._template = bg_picture.resize(self._pic_dims.outputSize)
        else:
            self._template = Image.new('RGB', self._pic_dims.outputSize,
                                       (255, 255, 255))

        overlay = self._cfg.get('Picture', 'overlay')
        if len(overlay) > 0:
            logging.info('Using overlay "{}"'.format(overlay))
            ov_picture = Image.open(overlay)
            self._overlay = ov_picture.resize(self._pic_dims.outputSize)
        else:
            self._overlay = Image.new('RGBA', self._pic_dims.outputSize,
                                      (255, 255, 255, 0))

        self.setIdle()
        self._comm.send(Workers.MASTER, StateMachine.CameraEvent('ready'))

    def teardown(self, state):

        if self._cap is not None:
            self._cap.cleanup()

    def run(self):

        for state in self._comm.iter(Workers.CAMERA):
            self.handleState(state)

        return True

    def handleState(self, state):

        if isinstance(state, StateMachine.StartupState):
            self.startup()
        elif isinstance(state, StateMachine.GreeterState):
            self.prepareCapture()
        elif isinstance(state, StateMachine.CountdownState):
            self.capturePreview()
        elif isinstance(state, StateMachine.CaptureState):
            if state.capturemode == StateMachine.CAPMODE_STATIC:
                self.capturePicture(state)
            elif state.capturemode == StateMachine.CAPMODE_BOOMERANG:
                self.captureVideo(state)
            else:
                raise TypeError('unknown capturemode in camera')
        elif isinstance(state, StateMachine.AssembleState):
            if state.capturemode == StateMachine.CAPMODE_STATIC:
                self.assemblePicture()
            elif state.capturemode == StateMachine.CAPMODE_BOOMERANG:
                self.assembleGIF()
            else:
                raise TypeError('unknown capturemode in camera')
        elif isinstance(state, StateMachine.TeardownState):
            self.teardown(state)

    def setActive(self):

        self._cap.setActive()

    def setIdle(self):

        if self._cap.hasIdle:
            self._cap.setIdle()

    def prepareCapture(self):

        self.setActive()
        self._pictures = []

    def capturePreview(self):

        if self._is_preview:
            while self._comm.empty(Workers.CAMERA):
                picture = self._cap.getPreview()
                if self._rotation is not None:
                    picture = picture.transpose(self._rotation)
                picture = picture.resize(self._pic_dims.previewSize)
                picture = ImageOps.mirror(picture)
                byte_data = BytesIO()
                picture.save(byte_data, format='jpeg')
                self._comm.send(Workers.GUI,
                                StateMachine.CameraEvent('preview', byte_data))

    def capturePicture(self, state):

        self.setIdle()
        picture = self._cap.getPicture()
        if self._rotation is not None:
            picture = picture.transpose(self._rotation)
        byte_data = BytesIO()
        picture.save(byte_data, format='jpeg')
        self._pictures.append(byte_data)
        self.setActive()

        if self._is_keep_pictures:
            self._comm.send(Workers.WORKER,
                            StateMachine.CameraEvent('capture', byte_data))

        if state.num_picture < self._pic_dims.totalNumPictures:
            self._comm.send(Workers.MASTER,
                            StateMachine.CameraEvent('countdown'))
        else:
            self._comm.send(Workers.MASTER,
                            StateMachine.CameraEvent('assemble'))

    def captureVideo(self, state):

        logging.debug('entering boomerang capture')
        number_pictures = 0

        counter = 0
        while number_pictures < self._gif_num_img_to_take:
            picture = self._cap.getPreview()
            if counter % self._gif_use_nth_capture == 0:
                # skip images inbetween
                number_pictures += 1
                if self._rotation is not None:
                    picture = picture.transpose(self._rotation)
                byte_data = BytesIO()
                picture.save(byte_data, format='jpeg')
                self._pictures.append(byte_data)
                if self._is_keep_pictures:
                    self._comm.send(Workers.WORKER,
                            StateMachine.CameraEvent('capture', byte_data))
            counter += 1

        self._comm.send(Workers.MASTER,
                        StateMachine.CameraEvent('assemble'))

    def assemblePicture(self):

        self.setIdle()

        picture = self._template.copy()
        for i in range(self._pic_dims.totalNumPictures):
            shot = Image.open(self._pictures[i])
            resized = shot.resize(self._pic_dims.thumbnailSize, Image.BICUBIC)
            picture.paste(resized, self._pic_dims.thumbnailOffset[i])
        picture.paste(self._overlay, (0, 0), self._overlay)

        byte_data = BytesIO()
        picture.save(byte_data, format='jpeg')
        self._comm.send(Workers.MASTER,
                        StateMachine.CameraEvent('review', byte_data))
        self._pictures = []

    def assembleGIF(self):

        self.setIdle()

        picture = []
        for i in range(self._gif_num_img_to_take):
            logging.debug("appending frame {}".format(i))
            picture.append(Image.open(self._pictures[i]))
        for i in range((self._gif_num_frames - self._gif_num_img_to_take), 0, -1):
            logging.debug("appending frame {}".format(i))
            picture.append(Image.open(self._pictures[i]))

        byte_data_gif = BytesIO()
        picture[0].save(byte_data_gif, format='GIF', append_images=picture[1:],
                        save_all=True, optimize=True, duration=self._gif_frame_duration,
                        loop=0)
        self._comm.send(Workers.MASTER,
                        StateMachine.CameraEvent('review', byte_data_gif, True))
        self._pictures = []
