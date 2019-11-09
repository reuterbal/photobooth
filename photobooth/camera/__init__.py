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
import math		   

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

        rot_vals = {0: None, 90: Image.ROTATE_90, 180: Image.ROTATE_180,
                    270: Image.ROTATE_270}
        self._rotation = rot_vals[self._cfg.getInt('Camera', 'rotation')]
        self._fancy = self._cfg.getBool('Picture', 'fancy')
        logging.info('fancy "{}"'.format(self._fancy))
        
    def startup(self):

        self._cap = self._cam()

        logging.info('Using camera {} preview functionality'.format(
            'with' if self._is_preview else 'without'))

        test_picture = self._cap.getPicture()
        if self._rotation is not None:
            test_picture = test_picture.transpose(self._rotation)

        self._pic_dims = PictureDimensions(self._cfg, test_picture.size)
        self._is_preview = self._is_preview and self._cap.hasPreview
        self._logo_rot = self._cfg.getInt('Picture', 'logo_rot')
        self._addlogo = self._cfg.getBool('Picture', 'addlogo')
        logging.info('Adding Logo : "{}"'.format(self._addlogo))

        logo_file = self._cfg.get('Picture', 'logo')
        if len(logo_file) > 0:
            logging.info('Using logo "{}"'.format(logo_file))
            self._logo = logo_file
        else:
            self._logo = Image.new('RGBA', (500,500),(155,0,0,0))

        background = self._cfg.get('Picture', 'background')
        addBg = self._cfg.getBool('Picture', 'addBg')
        bgColor = self._cfg.get('Picture', 'bgColor')
        if len(background) > 0 and addBg == True:
            logging.info('Using background "{}"'.format(background))
            bg_picture = Image.open(background)
            self._template = bg_picture.resize(self._pic_dims.outputSize)  #websta911 eventually add:  ,Image.ANTIALIAS
        else:
            bgCol = tuple(int(bgColor[i:i+2], 16) for i in (0, 2, 4))
            self._template = Image.new('RGB', self._pic_dims.outputSize,(bgCol))

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
            self.capturePicture(state)
        elif isinstance(state, StateMachine.AssembleState):
            self.assemblePicture()
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

    def assemblePicture_original(self):

        self.setIdle()

        picture = self._template.copy()
        for i in range(self._pic_dims.totalNumPictures):
            shot = Image.open(self._pictures[i])
            resized = shot.resize(self._pic_dims.thumbnailSize)
            picture.paste(resized, self._pic_dims.thumbnailOffset[i])

        byte_data = BytesIO()
        picture.save(byte_data, format='jpeg')
        self._comm.send(Workers.MASTER,
                        StateMachine.CameraEvent('review', byte_data))
        self._pictures = []
        
    def assemblePicture(self):
        """my custom Version of assembling Pictures"""
        self.setIdle()
        
        picture = self._template.copy()
        if(self._fancy):
            if(self._pic_dims.totalNumPictures == 3):
                # ----- 3 pictures rotated------
                outer_border = 30
                inner_border = 30
                pic_rotation = 11

                largePics_size = ( int( (self._pic_dims.outputSize[0] - ( outer_border *4))  // 10)*4.6   ,
                                int( (self._pic_dims.outputSize[1] - ( outer_border *4 ) )//10)*4.6)
                evenlargerPics_size = ( int( (self._pic_dims.outputSize[0] - ( outer_border *4))  // 10)*5.5   ,
                                int( (self._pic_dims.outputSize[1] - ( outer_border *4 ) )//10)*5.5)
                logo_size = ( int( (self._pic_dims.outputSize[0] ) //3 ),
                            int( (self._pic_dims.outputSize[1])//2 ) )
                #logo_size = (1206, 2669) #for hardcoded use
                logging.info('size largePicx "{}"'.format(largePics_size))
                logging.info('Size logo "{}"'.format(logo_size))

                # Image 0
                img = Image.open(self._pictures[0])
                img = img.convert('RGBA')
                img.thumbnail(largePics_size)
                logging.info('Image0 inserted with size pre rotation "{}"'.format(img.size))
                img = img.rotate(pic_rotation, expand=True)
                offset = ( outer_border  ,
                        outer_border  )
                picture.paste(img, offset, img)
                logging.info('Image0 inserted with size "{}"'.format(img.size))
                logging.info('largepic size "{}"'.format(largePics_size))

                # Image 1
                img = Image.open(self._pictures[1])
                img = img.convert('RGBA')
                img.thumbnail(largePics_size)
                img_norotated = img.size
                img_norotated_small = img.size
                img = img.rotate(pic_rotation, expand=True)
                img_small = img
                ta =  (img_norotated[1]+outer_border) * math.cos(math.radians(90 - pic_rotation)) ## a = Hypothenuse c * cosinus(beta), beta = 90° - Alpha 
                tb = math.sqrt(img_norotated[1] ** 2 - ta ** 2) #b = sqrt(c² - a²)
                logging.info('tb "{}"'.format(tb))
                logging.info('ta "{}"'.format(ta))
                logging.info('ta "{}"'.format((outer_border - round(ta))))
                #offset = ( (outer_border + round(ta)),  
                        #(self._pic_dims.outputSize[1] - outer_border - img.size[1]) ) #b = sqrt(c² - a²)
                #offset = ( ((self._pic_dims.outputSize[0] - outer_border*2 ) //2) - img.size[0],
                        #self._pic_dims.outputSize[1] - outer_border - img.size[1] )
                offset = ((outer_border + round(ta)),
                        (outer_border + round(tb) + outer_border ))
                img_small_offset = offset
                picture.paste(img, offset, img)
                logging.info('Image1 inserted with size "{}"'.format(img.size))

                # Image 2
                img = Image.open(self._pictures[2])
                img = img.convert('RGBA')
                img.thumbnail(evenlargerPics_size)
                img_norotated = img.size
                img = img.rotate(pic_rotation, expand=True)
                img_large = img
                #ta =  (img_norotated_small[1]) * math.cos(math.radians(90 - pic_rotation))
                #ta_d = outer_border * math.cos(math.radians(90 - pic_rotation))
                #tb_d = math.sqrt(outer_border ** 2 - ta_d ** 2)
                #tta = outer_border * math.tan(math.radians(90 - pic_rotation))
                #tta_c = math.sqrt(tta ** 2 + outer_border ** 2)

                da = img_norotated[0] * math.cos(math.radians(90 - pic_rotation)) # a calculate a of current picture to get distante from left upper corner of img 
                tda = da * math.tan(90 - pic_rotation) 

                #logging.info('ta_d "{}"'.format(ta_d))
                #logging.info('tb_d "{}"'.format(tb_d))
                #logging.info('ta "{}"'.format(ta))
                # offset = ( img.size[0] - round(ta)  + outer_border * 2  + round(tb_d) , ##original 
                #offset = ( img.size[0] - round(ta) + outer_border * 2 , ##working somehow use that in case of not knowing
                offset = ( img_small.size[0] - round(ta) + round(tda) ,
                        outer_border )
                #offset = ( (self._pic_dims.outputSize[0] - outer_border *2 ) //2,
                        #outer_border )
                img_large_offset = offset
                picture.paste(img, offset, img)
                logging.info('Image2 inserted')

                #Logo
                if(self._addlogo):
                    if len(self._logo) > 0:
                        logging.info('Using logo "{}"'.format(self._logo))
                        logo = Image.open(self._logo).convert("RGBA")
                        logo = logo.rotate(self._logo_rot, expand=True)
                        logo.thumbnail(logo_size, Image.ANTIALIAS)
                        #offset = (self._pic_dims.outputSize[0] - outer_border - logo.size[0] ,
                            #self._pic_dims.outputSize[1]  - outer_border- logo.size[1] )
                        rest_space = (((self._pic_dims.outputSize[0]-(img_small_offset[0] + img_small.size[0] + logo.size[0]))//2) ,
                                     ((self._pic_dims.outputSize[1]-(img_large_offset[1]+img_large.size[1]+logo.size[1]))//2))
                        offset = (img_small_offset[0] + img_small.size[0] + rest_space[0] , 
                                  img_large_offset[1]+img_large.size[1] + rest_space[1])
                        logging.info('Logo offset"{}"'.format(offset))
                        picture.paste(logo,offset,logo)
                        logging.info('Logo inserted')
                    else:
                        logging.info('No logo  defined')
                else:
                    logging.info('Addlogo set to FALSE')


        
            else:
                # 4 Pics + logo Layout
                #----------------- Layout 1 big 3 small-----

                outer_border = 40
                inner_border = 10

                smallPics_size = ( int( (self._pic_dims.outputSize[0] - ( outer_border * 2 ) - ( inner_border * 4 )) / 3 ) ,
                                    int( (self._pic_dims.outputSize[1] - ( outer_border * 2 ) - ( inner_border * 4 )) / 3 ))
                largePics_size = ( ( smallPics_size[0] * 2 ),
                            ( smallPics_size[1] * 2 ) )
                logo_size = ( int( (self._pic_dims.outputSize[0] - ( inner_border * 2 ) - ( outer_border ) - largePics_size[0]) ),
                                int( (self._pic_dims.outputSize[0] - ( inner_border * 2 ) - ( outer_border ) - smallPics_size[1]) ) )
                
                logging.info('Size logo "{}"'.format(logo_size))

                if(self._addlogo):
                    if len(self._logo) > 0:
                        logging.info('Using logo "{}"'.format(self._logo))
                        logo = Image.open(self._logo).convert("RGBA")
                        logo = logo.rotate(self._logo_rot, expand=True)
                        logo.thumbnail(logo_size, Image.ANTIALIAS)
                        offset = (((self._pic_dims.outputSize[0] - largePics_size[0] - outer_border - inner_border) // 2 ) - logo.size[0] // 2 ,
                            ((largePics_size[1]//2) + outer_border )- logo.size[1] //2)
                        logging.info('Logo offset"{}"'.format(offset))
                        picture.paste(logo,offset,logo)
                        logging.info('Logo inserted')
                    else:
                        logging.info('No logo  defined')
                else:
                    logging.info('Addlogo set to FALSE')

                # Image 0
                img = Image.open(self._pictures[0])
                img = img.convert('RGBA')
                #img = img.rotate(45, expand=True)
                img.thumbnail(largePics_size)
                offset = ( self._pic_dims.outputSize[0] - img.size[0] - outer_border - inner_border ,
                        outer_border )
                picture.paste(img, offset, img)
                logging.info('Image0 inserted with size "{}"'.format(img.size))

                # Image 1
                img = Image.open(self._pictures[1])
                img.thumbnail(smallPics_size)
                offset = ( outer_border + inner_border,
                        self._pic_dims.outputSize[1] - outer_border - img.size[1] )
                picture.paste(img, offset)
                logging.info('Image1 inserted')

                # Image 2
                img = Image.open(self._pictures[2])
                img.thumbnail(smallPics_size)
                offset = ( self._pic_dims.outputSize[0] // 2- img.size[0] // 2,
                        self._pic_dims.outputSize[1] - outer_border - img.size[1] )
                picture.paste(img, offset)
                logging.info('Image2 inserted')

                # Image 3
                img = Image.open(self._pictures[3])
                img.thumbnail(smallPics_size)
                offset = ( self._pic_dims.outputSize[0] - outer_border - img.size[0] - inner_border ,
                        self._pic_dims.outputSize[1] - outer_border - img.size[1] )
                picture.paste(img, offset)
                logging.info('Image3 inserted')
        
        else:
            for i in  range(self._pic_dims.totalNumPictures):
                logging.info('Pic "{}"'.format(i))
                shot = Image.open(self._pictures[i])
                resized = shot.resize(self._pic_dims.thumbnailSize)
                picture.paste(resized, self._pic_dims.thumbnailOffset[self._pic_dims.thumbsLocation[i]])
            
            if(self._addlogo):
                
                if len(self._logo) > 0:
                    logging.info('Using logo "{}"'.format(self._logo))
                    logo = Image.open(self._logo).convert("RGBA")
                    logo = logo.rotate(self._logo_rot, expand=True)
                    if(self._pic_dims.totalNumPictures < (self._pic_dims.numPictures[0] * self._pic_dims.numPictures[1])):
                        logo_size = ((self._pic_dims.thumbnailSize[0] / 100)*90,
                                    (self._pic_dims.thumbnailSize[1] / 100)*90)
                        logo.thumbnail(logo_size, Image.ANTIALIAS)
                        logopos = [i for i in range(self._pic_dims.numPictures[0] * self._pic_dims.numPictures[1]) if i not in self._pic_dims.thumbsLocation] # get postions without picture 
                        offset = ((self._pic_dims.thumbnailOffset[logopos[0]])[0]+ (self._pic_dims.thumbnailSize[0] -logo.size[0]) // 2, # calculate offsets for 1 logo on the first available postion
                                (self._pic_dims.thumbnailOffset[logopos[0]])[1]+ (self._pic_dims.thumbnailSize[1] -logo.size[1]) // 2)
                        
                    else:
                        logo_size = ((self._pic_dims.thumbnailSize[0] / 100)*70,
                                    (self._pic_dims.thumbnailSize[1] / 100)*70)
                        logo.thumbnail(logo_size, Image.ANTIALIAS)
                        offset = ((picture.size[0] - logo.size[0]) // 2,
                                (picture.size[1] - logo.size[1]) // 2)

                    picture.paste(logo,offset,logo)
                    logging.info('Logo inserted')
                else:
                    logging.info('No logo  defined')




        byte_data = BytesIO()
        picture.save(byte_data, format='jpeg')
        self._comm.send(Workers.MASTER,
                        StateMachine.CameraEvent('review', byte_data))
        self._pictures = []
