#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os.path

from time import localtime, strftime

from .PictureList import PictureList


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

    def __init__(self, config, queue):

        self._queue = queue


    def run(self):

        for func, args in iter(self._queue.get, 'teardown'):
            func(*args)

        return 0
