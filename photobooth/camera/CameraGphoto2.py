#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import logging

from PIL import Image

import gphoto2 as gp

from . import Camera


class CameraGphoto2(Camera):

    def __init__(self):

        super().__init__()

        self.hasPreview = True
        self.hasIdle = True

        logging.info('Using python-gphoto2 bindings')

        self._setupLogging()
        self._setupCamera()

    def cleanup(self):

        self._cap.set_config(self._oldconfig)
        self._cap.exit(self._ctxt)

    def _setupLogging(self):

        gp.error_severity[gp.GP_ERROR] = logging.WARNING
        gp.check_result(gp.use_python_logging())

    def _setupCamera(self):

        self._ctxt = gp.Context()
        self._cap = gp.Camera()
        self._cap.init(self._ctxt)

        logging.info('Camera summary: %s',
                     str(self._cap.get_summary(self._ctxt)))

        # get configuration tree
        # self._config = self._cap.get_config()
        # self._oldconfig = self._config
        config = self._cap.get_config()

        # make sure camera format is not set to raw
        imageformat = config.get_child_by_name('imageformat').get_value()
        if 'raw' in imageformat.lower():
            raise RuntimeError('Camera file format is set to RAW')

        self._printConfig(config)

    @staticmethod
    def _configTreeToText(tree, indent=0):

        config_txt = ''

        for chld in tree.get_children():
            config_txt += indent * ' '
            config_txt += chld.get_label() + ' [' + chld.get_name() + ']: '

            if chld.count_children() > 0:
                config_txt += '\n'
                config_txt += CameraGphoto2._configTreeToText(chld, indent + 4)
            else:
                config_txt += str(chld.get_value())
                try:
                    choice_txt = ' ('

                    for c in chld.get_choices():
                        choice_txt += c + ', '

                    choice_txt += ')'
                    config_txt += choice_txt
                except gp.GPhoto2Error:
                    pass
                config_txt += '\n'

        return config_txt

    @staticmethod
    def _printConfig(config):
        config_txt = 'Camera configuration:\n'
        config_txt += CameraGphoto2._configTreeToText(config)
        logging.info(config_txt)

    def setActive(self):

        config = self._cap.get_config()
        config.get_child_by_name('output').set_value('PC')
        self._cap.set_config(config)

    def setIdle(self):

        config = self._cap.get_config()
        config.get_child_by_name('output').set_value('Off')
        self._cap.set_config(config)

    def getPreview(self):

        camera_file = self._cap.capture_preview()
        file_data = camera_file.get_data_and_size()
        return Image.open(io.BytesIO(file_data))

    def getPicture(self):

        file_path = self._cap.capture(gp.GP_CAPTURE_IMAGE)
        camera_file = self._cap.file_get(file_path.folder, file_path.name,
                                         gp.GP_FILE_TYPE_NORMAL)
        file_data = camera_file.get_data_and_size()
        return Image.open(io.BytesIO(file_data))
