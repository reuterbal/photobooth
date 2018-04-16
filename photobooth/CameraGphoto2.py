#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io, logging

from PIL import Image

import gphoto2 as gp

from Camera import Camera


class CameraGphoto2(Camera):

    def __init__(self):

        super().__init__()

        self.hasPreview = True
        self.hasIdle = False
        self._isActive = False

        self._setupLogging()
        self._setupCamera()


    def cleanup(self):

        self._cap.exit(self._ctxt)
        # self.setIdle()


    def _setupLogging(self):

        logging.basicConfig(
            format='%(levelname)s: %(name)s: %(message)s', 
            level=logging.ERROR)
        gp.check_result(gp.use_python_logging())


    def _setupCamera(self):

        self._ctxt = gp.Context()
        self._cap = gp.Camera()
        self._cap.init(self._ctxt)

        self._printSummary()


        # get configuration tree
        config = gp.check_result(gp.gp_camera_get_config(self._cap))

        # find the image format config item
        OK, image_format = gp.gp_widget_get_child_by_name(config, 'imageformat')
        if OK >= gp.GP_OK:
            # get current setting
            value = gp.check_result(gp.gp_widget_get_value(image_format))
            # make sure it's not raw
            if 'raw' in value.lower():
                raise RuntimeError('Camera file format is set to RAW')

        print(config)


    def _printSummary(self):

        # self.setActive()

        text = self._cap.get_summary(self._ctxt)
        print('Summary')
        print('=======')
        print(str(text))

        # self.setIdle()


    # def setActive(self):

        # self._cap.init(self._ctxt)
        # if not self._isActive:
        #     self._cap.init(self._ctxt)
        #     self._isActive = True


    # def setIdle(self):

        # self._cap.exit(self._ctxt)
    #     if self._isActive:
    #         self._cap.exit(self._ctxt)
    #         self._isActive = False


    def getPreview(self):

        # self.setActive()
        camera_file = self._cap.capture_preview() #gp.check_result(gp.gp_camera_capture_preview(self._cap))
        file_data = camera_file.get_data_and_size() # gp.check_result(gp.gp_file_get_data_and_size(camera_file))
        return Image.open(io.BytesIO(file_data))


    def getPicture(self):
        
        # self.setActive()
        file_path = self._cap.capture(gp.GP_CAPTURE_IMAGE)
        camera_file = self._cap.file_get(file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL)
        file_data = camera_file.get_data_and_size()
        return Image.open(io.BytesIO(file_data))

